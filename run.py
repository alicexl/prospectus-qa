"""问答管线 CLI：python -X utf8 run.py --input questions.jsonl --output answers.jsonl"""
import json
import re
import sqlite3
import time
from pathlib import Path

import numpy as np

import llm
import schema
from ingest import get_conn, init_db

# ---------- RRF 融合 ----------
def rrf(*ranked_lists, k: int = 60) -> dict:
    """多路排序列表 → {key: score}，score=Σ1/(k+rank)。"""
    scores: dict = {}
    for lst in ranked_lists:
        for rank, item in enumerate(lst, start=1):
            key = item[0] if isinstance(item, (list, tuple)) else item
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
    return scores


# ---------- 实体链接 ----------
def _alias_core(alias: str) -> str:
    """全称去公司后缀 → 核心名（如 湖南国科微电子股份有限公司 → 湖南国科微电子）。"""
    for suf in ("股份有限公司", "有限责任公司", "有限公司", "公司"):
        if alias.endswith(suf) and len(alias) - len(suf) >= 4:
            return alias[: -len(suf)]
    return alias


def link_company(conn: sqlite3.Connection, question: str) -> str | None:
    """最长匹配 → doc_id：全称命中或核心名（≥4字）命中均可。匹配不到=知识库外。"""
    rows = conn.execute("SELECT alias, doc_id FROM company_registry").fetchall()
    best_len, best_doc = 0, None
    for alias, doc_id in rows:
        core = _alias_core(alias)
        hit_len = 0
        if alias in question:
            hit_len = len(alias)
        elif len(core) >= 4 and core in question:
            hit_len = len(core)
        if hit_len > best_len:
            best_len, best_doc = hit_len, doc_id
    return best_doc


# ---------- 路由（规则优先） ----------
_SQL_HINT = re.compile(r"基金|持仓|行情|份额|规模变动|持有人结构|日行情|涨跌幅|净值")
_DOC_HINT = re.compile(r"招股书|披露|募集|风险因素|发行股数|发行价格|营业收入|主营业务|承诺")


def route(conn: sqlite3.Connection, question: str, doc_id: str | None) -> str:
    if doc_id is None:
        return "sql" if _SQL_HINT.search(question) else "none"
    if _SQL_HINT.search(question) and (_DOC_HINT.search(question) or re.search(r"20\d\d", question)):
        return "hybrid"
    return "doc"


# ---------- 混合检索 ----------
def _fts_query(query: str) -> str:
    """净化成 FTS5 安全查询：中文/字母数字 token 化，≥3字（trigram 下限）引号包裹 OR 连接。"""
    toks = [t for t in re.findall(r"[一-鿿A-Za-z0-9]+", query) if len(t) >= 3][:8]
    return " OR ".join(f'"{t}"' for t in toks) if toks else '" impossibletoken "'


def _cos(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return float(a @ b / (na * nb)) if na and nb else 0.0


def search(conn: sqlite3.Connection, query: str, doc_id: str | None = None, k: int = 8) -> list[dict]:
    """BM25(FTS5 trigram) + 向量余弦 → RRF top-k（doc 路默认限单文档）。"""
    where, params = ("AND c.doc_id=?", [doc_id]) if doc_id else ("", [])
    try:
        bm = conn.execute(
            f"""SELECT c.chunk_id FROM chunks_fts f
                JOIN chunks c ON c.rowid = f.rowid
                WHERE chunks_fts MATCH ? {where}
                ORDER BY rank LIMIT 30""",
            [_fts_query(query)] + params).fetchall()
    except sqlite3.OperationalError:
        bm = []
    qvec = np.asarray(llm.embed([query])[0], dtype=np.float32)
    rows = conn.execute(
        f"SELECT chunk_id, doc_id, pdf_page, text, emb FROM chunks {'WHERE doc_id=?' if doc_id else ''}",
        params).fetchall()
    vecs = sorted(((r[0], _cos(qvec, np.frombuffer(r[4], dtype=np.float32)))
                   for r in rows if r[4]), key=lambda x: -x[1])
    scores = rrf([(r[0],) for r in bm], [(i,) for i, _ in vecs[:30]])
    by_id = {r[0]: r for r in rows}
    top = sorted(scores.items(), key=lambda kv: -kv[1])[:k]
    return [{"chunk_id": cid, "doc_id": by_id[cid][1], "pdf_page": by_id[cid][2],
             "text": by_id[cid][3], "rrf_score": s} for cid, s in top if cid in by_id]


# ---------- quote 程序化逐字校验 ----------
_FULL2HALF = str.maketrans("０１２３４５６７８９（）　：，。", "0123456789() :，.")


def norm_text(s: str) -> str:
    """规范化：全角→半角、去全部空白。quote 逐字匹配在此空间进行。"""
    return re.sub(r"\s+", "", s.translate(_FULL2HALF))


def verify_quote(conn: sqlite3.Connection, cite: dict) -> bool:
    """quote 必须能在 doc_id+pdf_page 对应页文本上逐字（规范化后）找到。"""
    row = conn.execute("SELECT text FROM pages WHERE doc_id=? AND pdf_page=?",
                       (cite["doc_id"], cite["pdf_page"])).fetchone()
    return bool(row) and norm_text(cite["quote"]) in norm_text(row[0])


# ---------- doc 路生成 ----------
_DOC_SYSTEM = """你是招股书问答助手。仅依据给出的资料片段回答，答案与引用必须逐字来自原文。
输出 JSON（不要其他文字）：{"answer": str, "answer_type": "number|text|list|refusal", "value": {"number": float|null, "unit": "元|万元|亿元|%|股|null"}, "items": [str], "citations": [{"pdf_page": int, "quote": str}], "confidence": 0到1}
规则：
- 数值只抄原文数字，禁止心算或换算；
- 信息在片段中不存在时 answer_type=refusal，并在 answer 说明（如"招股意向书阶段尚未确定发行价格"）；
- 引用 quote 必须是原文连续片段（≤80字），pdf_page 取片段所属页码；
- 若指标存在合并报表/母公司报表等不同口径或不同报告类型，须分别给出各口径数值并注明差异，每种口径各给一条引用。"""


def answer_doc(conn, question_id: str, question: str, doc_id: str) -> schema.AnswerRecord:
    chunks = search(conn, question, doc_id=doc_id, k=8)
    usage = {"input": 0, "output": 0}
    data: dict = {}
    if chunks:
        ctx = "\n\n".join(f"[片段 pdf_page={c['pdf_page']}]\n{c['text']}" for c in chunks)
        content, usage = llm.chat(_DOC_SYSTEM, f"问题：{question}\n\n资料：\n{ctx}")
        m = re.search(r"\{.*\}", content, re.S)
        data = json.loads(m.group(0)) if m else {}
    # 拒答判定③：检索置信不足
    top_score = chunks[0]["rrf_score"] if chunks else 0.0
    at = data.get("answer_type", "refusal")
    if not chunks or (top_score < 0.016 and at != "refusal"):
        at, data["answer"] = "refusal", "知识库中未检索到与问题充分相关的披露内容"
    # 引用逐字校验：校验不过的引用直接丢弃
    cites = []
    for ct in data.get("citations", []):
        cand = {"doc_id": doc_id, "pdf_page": int(ct.get("pdf_page", 0) or 0),
                "quote": str(ct.get("quote", ""))}
        if cand["pdf_page"] > 0 and cand["quote"] and verify_quote(conn, cand):
            pr = conn.execute("SELECT printed_page FROM pages WHERE doc_id=? AND pdf_page=?",
                              (doc_id, cand["pdf_page"])).fetchone()
            cites.append({**cand, "printed_page": pr[0] if pr else None})
    rec = schema.AnswerRecord(
        question_id=question_id,
        answer=str(data.get("answer", "")), answer_type=at,
        value=schema.Value(**(data.get("value") or {})),
        items=[str(i) for i in (data.get("items") or [])],
        citations=[schema.Citation(**c) for c in cites],
        route="doc", confidence=float(data.get("confidence", 0.5)), tokens=usage)
    # 有答案但引用全被校验毙掉 → 降级拒答（题目硬要求：每个答案都要有可逐字回溯的引用）
    if at != "refusal" and not cites:
        rec.answer_type, rec.answer, rec.confidence = "refusal", "引用无法在原文逐字验证", 0.0
    return rec


# ---------- 拒答辅助 ----------
def refuse(question_id: str, reason: str, route_v: str = "none") -> schema.AnswerRecord:
    return schema.AnswerRecord(question_id=question_id, answer=reason,
                               answer_type="refusal", route=route_v, confidence=0.0)


# ---------- 单题编排 ----------
def answer_one(conn, qid: str, question: str) -> schema.AnswerRecord:
    t0 = time.time()
    try:
        doc_id = link_company(conn, question)
        if doc_id is None:
            rec = refuse(qid, "知识库中不存在该公司（80份招股书未覆盖）", "none")
        else:
            r = route(conn, question, doc_id)
            if r == "sql":
                rec = answer_sql(conn, qid, question, doc_id)
            elif r == "hybrid":
                rec = answer_hybrid(conn, qid, question, doc_id)
                numeric_postprocess(question, rec,
                                    quote_texts=" ".join(c.quote for c in rec.citations))
            else:
                rec = answer_doc(conn, qid, question, doc_id)
                numeric_postprocess(question, rec,
                                    quote_texts=" ".join(c.quote for c in rec.citations))
    except Exception as e:  # noqa: BLE001 单题失败不中断整批
        rec = refuse(qid, f"处理失败：{e}")
    rec.latency_ms = int((time.time() - t0) * 1000)
    return rec


def main():
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    conn = get_conn()
    init_db(conn)
    with open(args.input, encoding="utf-8") as f, open(args.output, "w", encoding="utf-8") as out:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            rec = answer_one(conn, item["question_id"], item["question"])
            out.write(rec.model_dump_json() + "\n")
            out.flush()
            print(f"[done] {item['question_id']} -> {rec.answer_type}")


if __name__ == "__main__":
    main()


# ---------- 确定性数值计算（LLM 只出意图，不出结果） ----------
_UNIT_FACTOR = {"元": 1.0, "万元": 1e4, "亿元": 1e8, "%": 1.0, "股": 1.0}


def unit_convert(v: float, frm: str, to: str) -> float:
    return v * _UNIT_FACTOR[frm] / _UNIT_FACTOR[to]


def growth(base: float, now: float) -> float:
    return (now - base) / base


def eval_intent(intent: dict) -> dict:
    """执行 LLM 给出的结构化计算意图。growth/ratio 以 % 输出。"""
    op = intent["op"]
    if op == "convert":
        return {"number": unit_convert(intent["value"], intent["from"], intent["to"]),
                "unit": intent["to"]}
    if op == "growth":
        return {"number": round(growth(intent["base"], intent["now"]) * 100, 4), "unit": "%"}
    if op == "ratio":
        return {"number": round(intent["part"] / intent["total"] * 100, 4), "unit": "%"}
    if op == "sum":
        return {"number": sum(intent["values"]), "unit": intent.get("unit", "元")}
    raise ValueError(f"unknown op {op}")


_CALC_SYSTEM = """你负责把问题中的计算需求转成计算意图 JSON 数组，禁止自己算出结果。
可用 op：convert{value,from,to} growth{base,now} ratio{part,total} sum{values,unit}。
单位只允许：元/万元/亿元/%/股。数值直接用资料中已给出的原文数字。
只输出 JSON 数组（每个计算一个对象），无计算需求则输出 []。"""


def numeric_postprocess(question: str, rec: schema.AnswerRecord,
                        quote_texts: str = "") -> None:
    """answer_doc 之后：数值计算类问题用确定性工具重算 value（LLM 零心算）。
    多问句（如"是多少？增长多少？"）时主值进 value，全部结果写进 answer。"""
    if rec.answer_type != "number":
        return
    content, _u = llm.chat(_CALC_SYSTEM,
                           f"问题：{question}\n\n候选答案与原文数字：{rec.answer}\n{quote_texts[:2000]}")
    m = re.search(r"\[.*\]", content, re.S)
    try:
        intents = json.loads(m.group(0)) if m else []
    except json.JSONDecodeError:
        intents = []
    results = []
    for it in intents:
        try:
            results.append(eval_intent(it))
        except (KeyError, ValueError, ZeroDivisionError):
            continue
    if results:
        rec.value = schema.Value(**results[0])
        if len(results) > 1:
            extra = "；".join(f"{r['number']}{r.get('unit') or ''}" for r in results[1:])
            rec.answer = f"{rec.answer}（计算校验：{results[0]['number']}{results[0].get('unit') or ''}"
            rec.answer += f"；{extra}）"


# ---------- SQL 守卫 ----------
import sqlglot
from sqlglot import expressions as exp

_GUARD_BAD = (exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create, exp.Alter,
              exp.Pragma, exp.Attach, exp.Copy, exp.Command)


def sql_guard(sql: str) -> tuple[bool, str]:
    """白名单：单语句、纯 SELECT、无写/DDL/ATTACH/PRAGMA；自动强制 LIMIT 200。"""
    try:
        stmts = sqlglot.parse(sql, read="sqlite")
    except Exception:
        return False, ""
    if len(stmts) != 1 or not isinstance(stmts[0], exp.Select):
        return False, ""
    if stmts[0].find(*_GUARD_BAD):
        return False, ""
    if not stmts[0].args.get("limit"):
        sql = f"SELECT * FROM ({sql}) LIMIT 200"
    return True, sql


# ---------- 比赛库只读访问 + schema 卡片 ----------
COMPETITION_DB = str(Path("data/dataset/博金杯比赛数据.db").resolve())


def competition_ro() -> sqlite3.Connection:
    return sqlite3.connect(f"file:{COMPETITION_DB}?mode=ro", uri=True)


def build_schema_cards() -> str:
    ro = competition_ro()
    cards = []
    for (tname,) in ro.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
        cols = [r[1] for r in ro.execute(f'PRAGMA table_info("{tname}")')]
        n = ro.execute(f'SELECT COUNT(*) FROM "{tname}"').fetchone()[0]
        cards.append(f"表 {tname}（{n} 行）：{', '.join(cols)}")
    ro.close()
    return "\n".join(cards)


_SQL_SYSTEM = """你是 Text-to-SQL 助手。只输出一条只读 SQLite SELECT 语句，不要任何解释或 markdown。
字段名自带单位（如 收盘价(元)），日期字段按字符串比较（如 '2020-12-31'）。表名/字段名须与 Schema 完全一致。"""


def answer_sql(conn, qid: str, question: str, doc_id: str | None) -> schema.AnswerRecord:
    content, usage = llm.chat(_SQL_SYSTEM,
                              f"Schema：\n{build_schema_cards()}\n\n问题：{question}")
    sql = content.strip().removeprefix("```sql").removeprefix("```").removesuffix("```").strip()
    ok, safe_sql = sql_guard(sql)
    if not ok:
        return refuse(qid, "生成的 SQL 未通过安全校验，拒答", "sql")
    ro = competition_ro()
    cur = ro.execute(safe_sql)
    rows = cur.fetchmany(200)
    cols = [d[0] for d in cur.description] if cur.description else []
    ro.close()
    ans = "; ".join("，".join(f"{c}={v}" for c, v in zip(cols, r)) for r in rows[:10])
    return schema.AnswerRecord(question_id=qid, answer=ans or "查询无结果",
                               answer_type="text", sql=safe_sql, route="sql",
                               confidence=0.7, tokens=usage)


def answer_hybrid(conn, qid: str, question: str, doc_id: str) -> schema.AnswerRecord:
    """最小版：doc 路为主，sql 路结果拼进 answer，route=hybrid。"""
    rec = answer_doc(conn, qid, question, doc_id)
    try:
        srec = answer_sql(conn, qid, question, doc_id)
        if srec.sql:
            rec.sql, rec.route = srec.sql, "hybrid"
            rec.answer += f"｜数据库侧：{srec.answer}"
            rec.tokens = {"input": rec.tokens["input"] + srec.tokens["input"],
                          "output": rec.tokens["output"] + srec.tokens["output"]}
    except Exception:  # noqa: BLE001 sql 侧失败不拖垮 doc 侧
        pass
    return rec
