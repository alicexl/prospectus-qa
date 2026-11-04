"""标准答案标注流水线：确定性优先，LLM 辅助不定标。
CLI: python -X utf8 label.py --input questions/sample30.jsonl --output labels_pilot.jsonl [--review review_pilot.md]

流程（用户拍板）：
1 题型判定（sql/doc/hybrid，规则）
2 确定性优先：sql题=LLM生成SQL+程序执行与守卫；doc题=检索+引用逐字校验；计算=确定性意图执行
3 LLM 只负责解析/候选/定位，不独立定标
4 疑难题标 needs_review 进人工队列
5 产出 id/question/answer/evidence/verification_status
"""
import argparse
import json
import re
import sqlite3

import run
import schema
from ingest import get_conn, init_db


def classify(conn, question: str) -> tuple[str, str | None]:
    """题型 + doc_id。"""
    doc_id = run.link_company(conn, question)
    if doc_id is None:
        return ("sql" if run._SQL_HINT.search(question) else "none"), None
    if run._SQL_HINT.search(question) and (run._DOC_HINT.search(question)
                                           or re.search(r"20\d\d", question)):
        return "hybrid", doc_id
    return "doc", doc_id


def _norm(s: str) -> str:
    return run.norm_text(str(s))


_NUM_RE = re.compile(r"\d[\d,，.]*")


def answer_in_evidence(rec) -> bool:
    """确定性检查：答案锚点须能在已逐字验证的 quote 里找到。
    数字是事实类答案的主锚——LLM 会顺滑措辞/自加标点（s922 items 带全角冒号、
    s615 删「本公司的」），前缀逐字比对必误报；数字必须逐个在证据中（≥60%）。
    无数字答案退化为 items 前缀或答案前 20 字出自证据。"""
    ev = _norm(" ".join(c.quote for c in rec.citations))
    if not ev:
        return False
    claim = (rec.answer or "") + " " + " ".join(rec.items or [])
    nums = [n.replace(",", "").replace("，", "") for n in _NUM_RE.findall(claim)]
    if nums:
        hit = sum(1 for n in nums if n in ev.replace(",", ""))
        return hit / len(nums) >= 0.6
    if rec.items:
        return sum(1 for it in rec.items if _norm(it)[:12] and _norm(it)[:12] in ev) \
            >= max(1, (len(rec.items) + 1) // 2)
    if rec.value.number is not None:
        return re.sub(r",", "", f"{rec.value.number:g}") in ev.replace(",", "")
    return _norm(rec.answer)[:20] in ev  # 无数字 text：前 20 字出自证据


def _sql_is_simple(sql: str) -> bool:
    """单表无 JOIN/CASE 的查询 → 语义风险低，可自动采信。
    先剥掉我们自己的 LIMIT 包装壳（SELECT * FROM (...) LIMIT n）再判。"""
    s = sql.strip()
    if s.upper().startswith("SELECT * FROM (") and s.upper().endswith(") LIMIT 200"):
        s = s[s.index("(") + 1:s.rindex(")")].strip()
    u = s.upper()
    return " JOIN " not in u and "CASE" not in u and u.count("FROM") == 1


def label_one(conn, qid: str, question: str) -> dict:
    qtype, doc_id = classify(conn, question)
    multi_part = question.count("？") + question.count("?") > 1
    row = {"id": qid, "question": question, "qtype": qtype, "doc_id": doc_id,
           "answer": None, "answer_type": None, "value": None, "items": None,
           "evidence": None, "verification_status": None, "review_reasons": []}

    if qtype == "none":
        row.update(answer="知识库外且无DB关键词", answer_type="refusal",
                   evidence={"type": "none"},
                   verification_status="needs_review",
                   review_reasons=["无路由命中：需人工确认是否DB题措辞遗漏"])
        return row

    if qtype in ("sql", "hybrid"):
        rec = run.answer_sql(conn, qid, question, doc_id)
        ev = {"type": "sql", "sql": rec.sql, "result": rec.answer}
        if qtype == "hybrid":
            drec = run.answer_doc(conn, qid, question, doc_id)
            rec.answer = (rec.answer or "") + "｜文档侧：" + (drec.answer or "")
            ev["doc_citations"] = [{"pdf_page": c.pdf_page, "quote": c.quote}
                                   for c in drec.citations]
        row.update(answer=rec.answer, answer_type=rec.answer_type,
                   value=rec.value.model_dump(), items=rec.items, evidence=ev)
        reasons = []
        if not rec.sql:
            reasons.append("SQL生成/校验失败")
        elif "查询无结果" in (rec.answer or ""):
            reasons.append("SQL空结果（疑日期格式/条件过严）")
        elif not _sql_is_simple(rec.sql):
            reasons.append("多表JOIN/CASE：语义风险需人工核")
        if multi_part:
            reasons.append("多问句")
        row["verification_status"] = "auto_verified" if not reasons else "needs_review"
        row["review_reasons"] = reasons
        return row

    # doc 题：answer_one 含列表路/计算后处理
    rec = run.answer_one(conn, qid, question)
    ev = {"type": "doc_citations",
          "citations": [{"pdf_page": c.pdf_page, "printed_page": c.printed_page,
                         "quote": c.quote} for c in rec.citations]}
    row.update(answer=rec.answer, answer_type=rec.answer_type,
               value=rec.value.model_dump(), items=rec.items, evidence=ev)
    reasons = []
    if rec.answer_type == "refusal":
        if doc_id is None:
            row["verification_status"] = "auto_verified"  # 库外拒答（链接失败即证据）
            row["evidence"] = {"type": "outside_lib",
                               "note": "company_registry 无此公司"}
            return row
        reasons.append("库内公司但拒答：疑检索未命中或真未披露，须人工对PDF")
    else:
        if not answer_in_evidence(rec):
            reasons.append("答案值未出现在已验证quote中")
        if multi_part:
            reasons.append("多问句")
        if rec.value.number is not None and rec.value.number == 0:
            reasons.append("答案为0：常见假零，须人工核")
    row["verification_status"] = "auto_verified" if not reasons else "needs_review"
    row["review_reasons"] = reasons
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--review", default=None)
    args = ap.parse_args()
    conn = get_conn()
    init_db(conn)
    rows = []
    for line in open(args.input, encoding="utf-8"):
        if not line.strip():
            continue
        item = json.loads(line)
        r = label_one(conn, item["question_id"], item["question"])
        rows.append(r)
        print(f"[{r['verification_status']:>12}] {r['id']} {r['qtype']:<6} "
              f"{(r['answer'] or '')[:40]}", flush=True)
    with open(args.output, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    n_auto = sum(1 for r in rows if r["verification_status"] == "auto_verified")
    print(f"\n共 {len(rows)} 题：auto_verified {n_auto} / needs_review {len(rows) - n_auto}")
    if args.review:
        with open(args.review, "w", encoding="utf-8") as f:
            f.write("# 人工复核队列\n\n| id | 题型 | 复核原因 | 系统答案 | 证据 |\n|---|---|---|---|---|\n")
            for r in rows:
                if r["verification_status"] == "needs_review":
                    ev = r["evidence"] or {}
                    ev_s = (ev.get("sql") or "；".join(
                        c["quote"][:40] for c in ev.get("citations", [])) or "")[:80]
                    f.write(f"| {r['id']} | {r['qtype']} | {'；'.join(r['review_reasons'])} "
                            f"| {(r['answer'] or '')[:60]} | {ev_s} |\n")
        print(f"复核队列 → {args.review}")


if __name__ == "__main__":
    main()
    import os
    os._exit(0)  # openai/truststore 在 Windows 解释器退出时悬挂（工作已落盘，跳过清理）
