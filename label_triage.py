"""复核队列分层消化：JOIN题=独立第二SQL交叉验证；多问句doc题=数字锚点重算。
CLI: python -X utf8 label_triage.py   # 读 labels_full.jsonl → 原地升级状态
"""
import json
import re

import run
from ingest import get_conn, init_db


def _norm(s: str) -> str:
    return run.norm_text(str(s or ""))


def cross_check_sql(conn, row) -> str:
    """独立重生成一条 SQL 执行，与已存答案比对。
    返回 cross_verified / conflict / fail。"""
    try:
        rec = run.answer_sql(conn, row["id"], row["question"], row.get("doc_id"))
    except Exception:  # noqa: BLE001
        return "fail"
    if not rec.sql or not rec.answer:
        return "fail"
    if _norm(rec.answer) == _norm(row["answer"] or ""):
        return "cross_verified"
    # 数字主锚比对（格式化差异容忍：两次SQL的展示串可能不同但数值一致）
    nums_new = re.findall(r"\d[\d,，.]*", rec.answer or "")
    nums_old = re.findall(r"\d[\d,，.]*", row["answer"] or "")
    strip = lambda xs: sorted(x.replace(",", "").replace("，", "") for x in xs)  # noqa: E731
    if nums_new and nums_old and strip(nums_new) == strip(nums_old):
        return "cross_verified"
    return "conflict"


def anchor_check(row) -> str:
    """doc 多问句：重算 答案数字锚点 ⊆ 已验证 quotes。"""
    ev = row.get("evidence") or {}
    quotes = [c.get("quote", "") for c in ev.get("citations", [])]
    evn = _norm(" ".join(quotes))
    if not evn:
        return "conflict"
    claim = (row.get("answer") or "") + " " + " ".join(row.get("items") or [])
    nums = [n.replace(",", "").replace("，", "")
            for n in re.findall(r"\d[\d,，.]*", claim)]
    if not nums:
        return "fail"
    hit = sum(1 for n in nums if n in evn.replace(",", ""))
    return "cross_verified" if hit / len(nums) >= 0.8 else "conflict"


def main():
    conn = get_conn()
    init_db(conn)
    rows = [json.loads(l) for l in open("labels_full.jsonl", encoding="utf-8")]
    out = []
    stat = {"cross_verified": 0, "conflict": 0, "fail": 0, "kept_review": 0}
    for r in rows:
        if r["verification_status"] != "needs_review":
            out.append(r)
            continue
        reasons = set(r.get("review_reasons") or [])
        only_join = reasons <= {"多表JOIN/CASE：语义风险需人工核"}
        doc_multipart = "多问句" in reasons and r["qtype"] == "doc" \
            and reasons <= {"多问句"}
        if only_join and r["qtype"] in ("sql", "hybrid"):
            v = cross_check_sql(conn, r)
            if v == "cross_verified":
                r["verification_status"] = "cross_verified"
                r["evidence"]["cross_check"] = "second_sql_agrees"
            else:
                r["review_reasons"].append(f"交叉验证{v}")
            stat[v] += 1
        elif doc_multipart:
            v = anchor_check(r)
            if v == "cross_verified":
                r["verification_status"] = "cross_verified"
                r["evidence"]["cross_check"] = "number_anchor_recheck"
            else:
                r["review_reasons"].append(f"锚点复算{v}")
            stat[v] += 1
        else:
            stat["kept_review"] += 1
        out.append(r)
        if (len(out)) % 50 == 0:
            print(f"[progress] {len(out)}/{len(rows)}", flush=True)
    with open("labels_full.jsonl", "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    from collections import Counter
    print("终态:", dict(Counter(r["verification_status"] for r in out)))
    print("消化:", stat)


if __name__ == "__main__":
    main()
    import os
    os._exit(0)
