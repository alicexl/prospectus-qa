"""问答管线 CLI：python -X utf8 run.py --input questions.jsonl --output answers.jsonl"""
import json
import math
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
_JIEBA_DICT_LOADED = False


def _load_company_dict(conn: sqlite3.Connection) -> None:
    """把 80 家公司别名注入 jieba 词典（未登录公司名会被 HMM 切碎：
    中海达→中海/达，真兰仪表→真兰/仪表）。成词后链接与 BM25 都受益。"""
    global _JIEBA_DICT_LOADED
    if _JIEBA_DICT_LOADED:
        return
    for (alias,) in conn.execute("SELECT DISTINCT alias FROM company_registry").fetchall():
        if len(alias) >= 3:
            jieba.add_word(alias, freq=10_000_000)
            core = _alias_core(alias)
            if len(core) >= 3:
                jieba.add_word(core, freq=10_000_000)
    _JIEBA_DICT_LOADED = True


def _alias_core(alias: str) -> str:
    """全称去公司后缀 → 核心名（如 湖南国科微电子股份有限公司 → 湖南国科微电子）。"""
    for suf in ("股份有限公司", "有限责任公司", "有限公司", "公司"):
        if alias.endswith(suf) and len(alias) - len(suf) >= 4:
            return alias[: -len(suf)]
    return alias


def link_company(conn: sqlite3.Connection, question: str) -> str | None:
    """最长匹配 → doc_id：全称 / 核心名（去公司后缀）⊆ 问题。匹配不到=知识库外。
    简称/变体写法靠 company_registry 手动别名（ingest.MANUAL_ALIASES）直配，
    不做 n-gram 猜测——猜错比拒答更糟（q8「湖南长远锂业」曾误链「湖南长远锂科」）。"""
    rows = conn.execute("SELECT alias, doc_id FROM company_registry").fetchall()
    _load_company_dict(conn)
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


# ---------- 路由（规则优先，无 LLM 兜底） ----------
# DB 领域词表：纯 DB 题（基金/行情/行业）题面无招股书公司名，实体链接落空后
# 命中即走 sql 路优先处理——这些领域词几乎不出现在文档事实题里，误判率很低。
# 增补规则：新增 DB 领域题漏路由时，把领域词补进词表即可（改动机会少，直接常量）。
_SQL_WORDS = ("持有人结构", "规模变动", "行业划分", "行业分类", "一级行业", "二级行业",
              "成交金额", "日收益率", "股票代码", "日行情", "涨跌幅",
              "基金", "持仓", "行情", "份额", "净值", "申万", "中信",
              "振幅", "收盘", "开盘", "港股", "A股公司", "上市公司")
# 文档领域词表：命中按文档路处理；与 DB 词同时命中 → hybrid。
_DOC_WORDS = ("风险因素", "发行股数", "发行价格", "营业收入", "主营业务",
              "招股书", "披露", "募集", "承诺")
_SQL_HINT = re.compile("|".join(_SQL_WORDS))
_DOC_HINT = re.compile("|".join(_DOC_WORDS))


# hybrid 触发：DB 词命中且题面另有文档语境（文档词或年份）。
# 多问句题「2016年营收多少？基金持仓多少？」doc 与 DB 两者都要查。
_YEAR_RE = re.compile(r"20\d\d")


def route(conn: sqlite3.Connection, question: str, doc_id: str | None) -> str:
    if doc_id is None:
        return "sql" if _SQL_HINT.search(question) else "none"
    if _SQL_HINT.search(question) and (_DOC_HINT.search(question) or _YEAR_RE.search(question)):
        return "hybrid"
    return "doc"


# ---------- 混合检索（ragbot 同构：scope-then-score——doc圈定后库内/内存打分） ----------
import jieba
from collections import Counter

_WORD = re.compile(r"[一-鿿A-Za-z0-9]+")


def _tokens(text: str) -> list[str]:
    """jieba 词级 token（内存 BM25 无 3 字下限，2 字词直接可用）。"""
    return [t for t in jieba.lcut(re.sub(r"(?<![0-9])(19|20)\d{2}(?![0-9])\s*年?", "", text))
            if _WORD.fullmatch(t)]


_TOK_CACHE: dict[str, dict[int, list[str]]] = {}  # doc_id -> {chunk_id: tokens}


def _doc_tokens(conn, doc_id: str, rows: list[tuple]) -> list[tuple[int, list[str]]]:
    """chunk 分词带进程内缓存（现切 1800 chunk ≈2s，同 doc 多题复用）。"""
    cache = _TOK_CACHE.get(doc_id)
    if cache is None:
        cache = {r[0]: _tokens(r[3]) for r in rows}
        _TOK_CACHE[doc_id] = cache
    return [(r[0], cache[r[0]]) for r in rows]


def _bm25(query_toks: list[str], doc_chunks: list[tuple[int, list[str]]],
          k1: float = 1.5, b: float = 0.75) -> list[tuple[int, float]]:
    """内存 Okapi BM25，doc 内 IDF（scope-then-score：圈定后才打分，
    不做全库 FTS 扫描——trigram OR 全库打分实测慢一个数量级）。"""
    N = len(doc_chunks)
    if not N or not query_toks:
        return []
    df = Counter()
    tf: dict[int, Counter] = {}
    lens = {}
    for cid, toks_ in doc_chunks:
        c = Counter(toks_)
        tf[cid] = c
        lens[cid] = len(toks_) or 1
        for t in query_toks:
            if t in c:
                df[t] += 1
    avgdl = sum(lens.values()) / N
    qset = set(query_toks)
    out = []
    for cid in tf:
        s = 0.0
        for t in qset:
            f = tf[cid].get(t, 0)
            if not f:
                continue
            idf = math.log(1 + (N - df[t] + 0.5) / (df[t] + 0.5))
            denom = f + k1 * (1 - b + b * lens[cid] / avgdl)
            s += idf * f * (k1 + 1) / denom
        if s > 0:
            out.append((cid, s))
    out.sort(key=lambda x: -x[1])
    return out


def _cos(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return float(a @ b / (na * nb)) if na and nb else 0.0


def search(conn: sqlite3.Connection, query: str, doc_id: str | None = None, k: int = 8) -> list[dict]:
    """doc 圈定 → 内存 BM25(jieba) + 向量余弦 → RRF top-k。"""
    where, params = ("WHERE doc_id=?", [doc_id]) if doc_id else ("", [])
    rows = conn.execute(
        f"SELECT chunk_id, doc_id, pdf_page, text, emb FROM chunks {where}", params).fetchall()
    if not rows:
        return []
    q_toks = _tokens(query)
    doc_chunks = _doc_tokens(conn, doc_id or "", rows)
    bm = _bm25(q_toks, doc_chunks)[:30]
    qvec = np.asarray(llm.embed([query])[0], dtype=np.float32)
    vecs = sorted(((r[0], _cos(qvec, np.frombuffer(r[4], dtype=np.float32)))
                   for r in rows if r[4]), key=lambda x: -x[1])
    scores = rrf([(i,) for i, _ in bm], [(i,) for i, _ in vecs[:30]])
    by_id = {r[0]: r for r in rows}
    top = sorted(scores.items(), key=lambda kv: -kv[1])[:k]
    out = [{"chunk_id": cid, "doc_id": by_id[cid][1], "pdf_page": by_id[cid][2],
            "text": by_id[cid][3], "rrf_score": s} for cid, s in top if cid in by_id]
    # 文本chunk入选 → 同页表格chunk自动带上（表格bbox已从正文剔除，是文本的数值补充）
    if doc_id and out:
        got = {o["chunk_id"] for o in out}
        pages_hit = {o["pdf_page"] for o in out}
        ph = ",".join("?" * len(pages_hit))
        for r in conn.execute(
                f"SELECT chunk_id, doc_id, pdf_page, text FROM chunks "
                f"WHERE doc_id=? AND pdf_page IN ({ph}) AND text LIKE '[表格%'", [doc_id, *pages_hit]):
            if r[0] not in got and len(out) < k + 6:
                out.append({"chunk_id": r[0], "doc_id": r[1], "pdf_page": r[2],
                            "text": r[3], "rrf_score": 0.0})
    return out


# ---------- quote 程序化逐字校验 ----------
_FULL2HALF = str.maketrans("０１２３４５６７８９（）　：，。", "0123456789() :，.")


def norm_text(s: str) -> str:
    """规范化：全角→半角、去全部空白。quote 逐字匹配在此空间进行。"""
    return re.sub(r"\s+", "", s.translate(_FULL2HALF))


def verify_quote(conn: sqlite3.Connection, cite: dict) -> bool:
    """quote 必须能在 doc_id+pdf_page 对应页逐字（规范化后）找到。
    页文本不含表格区域（bbox 已剔除），表格内容在 blocks 里——两者并集校验。"""
    page = conn.execute("SELECT text FROM pages WHERE doc_id=? AND pdf_page=?",
                        (cite["doc_id"], cite["pdf_page"])).fetchone()
    if not page:
        return False
    texts = [page[0]] + [r[0] for r in conn.execute(
        "SELECT text FROM blocks WHERE doc_id=? AND pdf_page=? AND type='table'",
        (cite["doc_id"], cite["pdf_page"])).fetchall()]
    nq = norm_text(cite["quote"])
    return any(nq in norm_text(t) for t in texts)


def strip_company(conn: sqlite3.Connection, question: str, doc_id: str) -> str:
    """检索前剥离公司别名：doc 已锁定，query 里的公司名只会在向量侧匹配到
    每页页眉（页页含公司名），挤掉真正含答案的 chunk。"""
    q = question
    aliases = [r[0] for r in conn.execute(
        "SELECT alias FROM company_registry WHERE doc_id=?", (doc_id,)).fetchall()]
    for a in sorted(aliases, key=len, reverse=True):
        q = q.replace(a, "")
    return q.strip() or question


# ---------- doc 路生成 ----------
_DOC_SYSTEM = """你是招股书问答助手。仅依据给出的资料片段回答，答案与引用必须逐字来自原文。
输出 JSON（不要其他文字）：{"answer": str, "answer_type": "number|text|list|refusal", "value": {"number": float|null, "unit": "元|万元|亿元|%|股|null"}, "items": [str], "citations": [{"pdf_page": int, "quote": str}], "confidence": 0到1}
规则：
- 数值只抄原文数字，禁止心算或换算；
- 信息在片段中不存在时 answer_type=refusal，并在 answer 说明（如"招股意向书阶段尚未确定发行价格"）；
- 引用 quote 必须是原文连续片段（≤80字），pdf_page 取片段所属页码；
- 若指标存在合并报表/母公司报表等不同口径或不同报告类型，须分别给出各口径数值并注明差异，每种口径各给一条引用。"""


def answer_doc(conn, question_id: str, question: str, doc_id: str) -> schema.AnswerRecord:
    q_ret = strip_company(conn, question, doc_id)  # 检索用剥公司名的query
    chunks = search(conn, q_ret, doc_id=doc_id, k=10)
    usage = {"input": 0, "output": 0}
    data: dict = {}
    if chunks:
        ctx = "\n\n".join(f"[片段 pdf_page={c['pdf_page']}]\n{c['text']}" for c in chunks)
        content, usage = llm.chat(_DOC_SYSTEM, f"问题：{question}\n\n资料：\n{ctx}")
        m = re.search(r"\{.*\}", content, re.S)
        data = json.loads(m.group(0)) if m else {}
    # 拒答判定③：检索置信不足（0.012=单路 RRF top8 可达；两路齐时 top1≈0.033）
    top_score = chunks[0]["rrf_score"] if chunks else 0.0
    at = data.get("answer_type", "refusal")
    if not chunks or (top_score < 0.012 and at != "refusal"):
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
    dv = dict(data.get("value") or {})
    try:
        if dv.get("number") is not None:
            dv["number"] = _num(dv["number"])  # LLM 可能吐带逗号字符串数字
    except ValueError:
        dv["number"] = None
    if dv.get("unit") not in ("元", "万元", "亿元", "%", "股"):  # 题目枚举外的单位(次/人/家)置None
        dv["unit"] = None
    rec = schema.AnswerRecord(
        question_id=question_id,
        answer=str(data.get("answer", "")), answer_type=at,
        value=schema.Value(**dv),
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
        r = route(conn, question, doc_id)
        if r == "none":
            rec = refuse(qid, "知识库中不存在该公司", "none")
        elif r == "sql":
            # 纯 DB 题：实体链接失败但 DB 领域词命中（无文档实体）
            rec = answer_sql(conn, qid, question, doc_id)
        else:
            # 长列表题（列出/有哪些X）：题面点名节标题 或 兜底章节关键词 → 章节全量召回
            if r == "doc" and _LIST_HINT.search(question):
                kw = _section_kw(conn, question, doc_id) or _fallback_kw(question)
                if kw:
                    rec = answer_listq(conn, qid, question, doc_id, kw)
                    rec.latency_ms = int((time.time() - t0) * 1000)
                    return rec
            if r == "hybrid":
                rec = answer_hybrid(conn, qid, question, doc_id)
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


# ---------- 确定性数值计算（LLM 只出意图，不出结果） ----------
_UNIT_FACTOR = {"元": 1.0, "万元": 1e4, "亿元": 1e8, "%": 1.0, "股": 1.0}


def _num(v) -> float:
    """LLM 可能吐带逗号字符串数字（flash 实测 "1,684.4092"），统一强转。"""
    return float(str(v).replace(",", ""))


def unit_convert(v: float, frm: str, to: str) -> float:
    return v * _UNIT_FACTOR[frm] / _UNIT_FACTOR[to]


def growth(base: float, now: float) -> float:
    return (now - base) / base


def eval_intent(intent: dict) -> dict:
    """执行 LLM 给出的结构化计算意图。growth/ratio 以 % 输出。"""
    op = intent["op"]
    if op == "convert":
        return {"number": unit_convert(_num(intent["value"]), intent["from"], intent["to"]),
                "unit": intent["to"]}
    if op == "growth":
        return {"number": round(growth(_num(intent["base"]), _num(intent["now"])) * 100, 4),
                "unit": "%"}
    if op == "ratio":
        return {"number": round(_num(intent["part"]) / _num(intent["total"]) * 100, 4),
                "unit": "%"}
    if op == "sum":
        return {"number": sum(_num(v) for v in intent["values"]), "unit": intent.get("unit", "元")}
    raise ValueError(f"unknown op {op}")


_CALC_SYSTEM = """你负责把问题中的计算需求转成计算意图 JSON 数组，禁止自己算出结果。
可用 op：convert{value,from,to} growth{base,now} ratio{part,total} sum{values,unit}。
单位只允许：元/万元/亿元/%/股。数值直接用资料中已给出的原文数字。
数组第一个元素对应问题第一问的主数值（如"营业收入是多少"→该营收值本身），growth/ratio 等衍生计算排在后面。
问题问"增长多少/增速"且资料给出两期数值时，必须输出 growth 意图（base=前期, now=本期）。
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
        sample = ro.execute(f'SELECT * FROM "{tname}" LIMIT 1').fetchone()
        s_txt = "，".join(f"{c}={v}" for c, v in zip(cols, sample))[:150] if sample else ""
        cards.append(f"表 {tname}（{n} 行）：{', '.join(cols)}\n  样例行：{s_txt}")
    ro.close()
    return "\n".join(cards)


_SQL_SYSTEM = """你是 Text-to-SQL 助手。只输出一条只读 SQLite SELECT 语句，不要任何解释或 markdown。
字段名自带单位（如 收盘价(元)），带括号/特殊字符的字段名必须用双引号包裹。
无别名的表达式列必须用 AS 起简短别名（如 AS 结果）——否则列名会变成整条表达式。
日期字段格式各表不统一（有的表是 '20191231'，有的是 '2019-03-31 00:00:00'）——
先看该表样例行的实际格式，用完全相同的格式做等值或前缀 LIKE 匹配。
枚举字段用完整枚举值（如 行业划分标准 的取值是 '中信行业分类'/'申万行业分类'，不是'申万'）。
表名/字段名须与 Schema 完全一致。"""


def _run_sql(safe_sql: str) -> tuple[list[tuple], list[str]]:
    ro = competition_ro()
    try:
        cur = ro.execute(safe_sql)
        rows = cur.fetchmany(200)
        cols = [d[0] for d in cur.description] if cur.description else []
        return rows, cols
    finally:
        ro.close()


def answer_sql(conn, qid: str, question: str, doc_id: str | None) -> schema.AnswerRecord:
    usage = {"input": 0, "output": 0}
    prompt = f"Schema：\n{build_schema_cards()}\n\n问题：{question}"
    content, u = llm.chat(_SQL_SYSTEM, prompt)
    usage = {"input": u["input"], "output": u["output"]}
    for attempt in range(2):  # 执行错误给一次自纠错重试
        sql = content.strip().removeprefix("```sql").removeprefix("```").removesuffix("```").strip()
        parts = [p for p in sql.split(";") if p.strip()]  # 拆多语句只取第一条
        sql = parts[0].strip() if parts else sql
        ok, safe_sql = sql_guard(sql)
        if not ok:
            return refuse(qid, "生成的 SQL 未通过安全校验，拒答", "sql")
        try:
            rows, cols = _run_sql(safe_sql)
        except sqlite3.Error as e:
            if attempt == 0:
                content, u2 = llm.chat(
                    _SQL_SYSTEM,
                    f"{prompt}\n\n你之前的SQL：{safe_sql}\n执行报错：{e}\n"
                    f"请修正（字段名须与Schema完全一致），只输出一条SELECT语句")
                usage["input"] += u2["input"]
                usage["output"] += u2["output"]
                continue
            return refuse(qid, f"SQL 执行失败：{e}", "sql")
        if not rows and attempt == 0:
            # 空结果≠正确：常见根因=枚举字段写了不完整值（年报 vs '年报(含半年报)'）
            # 或日期格式错——喂回空结果让模型自查一轮
            content, u2 = llm.chat(
                _SQL_SYSTEM,
                f"{prompt}\n\n你之前的SQL：{safe_sql}\n执行结果为空。\n"
                f"自查：①枚举字段是否用了不完整值（等值可放宽为 LIKE 前缀，"
                f"如 报告类型 LIKE '年报%'）；②日期格式是否与样例行一致；"
                f"③过滤条件是否过严。只输出一条修正后的SELECT语句")
            usage["input"] += u2["input"]
            usage["output"] += u2["output"]
            continue
        # 无别名表达式列名=整个SQL文本（s75 教训），超 20 字以「结果」替代
        ans = "; ".join("，".join(f"{(c if len(c) <= 20 else '结果')}={v}"
                                  for c, v in zip(cols, r)) for r in rows[:10])
        return schema.AnswerRecord(question_id=qid, answer=ans or "查询无结果",
                                   answer_type="text", sql=safe_sql, route="sql",
                                   confidence=0.7, tokens=usage)
    return refuse(qid, "SQL 生成失败", "sql")


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


# ---------- 长列表：章节定位 + 整章召回 ----------
_SEC_LINE = re.compile(r"^第[一二三四五六七八九十百]+节\s*(\S.{0,19})$")


def _sec_heading(text: str) -> str | None:
    """取 chunk 前 3 行中的节标题行（行首锚定，防正文引用"第四节 风险因素"误触发）。"""
    for line in text.split("\n")[:3]:
        m = _SEC_LINE.match(line.strip())
        if m:
            return m.group(1).strip().rstrip("… .。")
    return None


def locate_section_chunks(conn, doc_id: str, section_kw: str) -> list[dict]:
    """标题树找章节起点（如「风险因素」），收录到下一节标题前的全部 chunks——
    长列表完整性靠整章召回而非 top-k。"""
    allc = conn.execute(
        "SELECT chunk_id, pdf_page, text FROM chunks WHERE doc_id=? ORDER BY pdf_page, chunk_id",
        (doc_id,)).fetchall()
    inside, started = [], False
    for cid, pg, text in allc:
        head = _sec_heading(text)
        if head is not None:
            if started:
                break  # 下一节开始 → 收束
            started = section_kw in head
        if started:
            inside.append({"chunk_id": cid, "doc_id": doc_id, "pdf_page": pg, "text": text})
    return inside


_LIST_HINT = re.compile(r"列出|全部|有哪些|分别有哪些")

# 长列表路兜底章节：招股书两大列表章节（风险因素/募投项目），条目多、跨多页、
# top-k 检索必漏——题面提及章节关键词即整章召回。发现新的长列表章节题型时补词。
_LIST_FALLBACK = (("风险", "风险因素"), ("募集", "募集"))


def _fallback_kw(question: str) -> str | None:
    """题面提及兜底章节关键词 → 对应章节名，否则 None。"""
    return next((sec for key, sec in _LIST_FALLBACK if key in question), None)


def _section_kw(conn, question: str, doc_id: str) -> str | None:
    """「列出X」类题的目标章节名：遍历 doc 全部节标题，标题 ⊆ 题面取最长命中
    （q6「列出…全部风险因素」→ 风险因素）。"""
    heads: set[str] = set()
    for (text,) in conn.execute("SELECT text FROM chunks WHERE doc_id=?", (doc_id,)):
        h = _sec_heading(text)
        if h:
            heads.add(h)
    return max((h for h in heads if h in question), key=len, default=None)


def answer_listq(conn, qid: str, question: str, doc_id: str,
                 kw: str | None = None) -> schema.AnswerRecord:
    """「列出全部X」类：章节全量召回 → LLM 按层级结构化 → items+条目数（程序校验计数）。
    kw=章节名：题面点名的节标题优先，兜底章节表（_LIST_FALLBACK）次之，均无 → 拒答。"""
    kw = kw or _section_kw(conn, question, doc_id) or _fallback_kw(question)
    if not kw:
        return refuse(qid, "未能在知识库中定位相关章节内容", "doc")
    secs = locate_section_chunks(conn, doc_id, kw)
    usage = {"input": 0, "output": 0}
    items: list[str] = []
    cites: list[dict] = []
    if secs:
        ctx = "\n\n".join(f"[pdf_page={s['pdf_page']}]\n{s['text']}" for s in secs[:60])
        sysp = """你是招股书结构化助手。按原文层级列出全部条目，禁止增删改写。
输出 JSON（不要其他文字）：{"items": [str], "citations": [{"pdf_page": int, "quote": str}]}
items 每项一条（风险因素类带类别前缀如"技术风险-产品迭代风险"）；quote 为该项在原文的连续片段（≤80字）。"""
        content, usage = llm.chat(sysp, f"问题：{question}\n\n章节内容：\n{ctx}")
        m = re.search(r"\{.*\}", content, re.S)
        data = json.loads(m.group(0)) if m else {}
        items = [str(i) for i in (data.get("items") or [])]
        for ct in data.get("citations", []):
            cand = {"doc_id": doc_id, "pdf_page": int(ct.get("pdf_page", 0) or 0),
                    "quote": str(ct.get("quote", ""))}
            if cand["pdf_page"] > 0 and cand["quote"] and verify_quote(conn, cand):
                pr = conn.execute("SELECT printed_page FROM pages WHERE doc_id=? AND pdf_page=?",
                                  (doc_id, cand["pdf_page"])).fetchone()
                cites.append({**cand, "printed_page": pr[0] if pr else None})
    n = len(items)
    if n == 0:
        return refuse(qid, "未能在知识库中定位相关章节内容", "doc")
    return schema.AnswerRecord(
        question_id=qid, answer=f"共 {n} 项", answer_type="list",
        items=items, citations=[schema.Citation(**c) for c in cites],
        route="doc", confidence=0.8 if cites else 0.3, tokens=usage)


if __name__ == "__main__":
    main()
