"""问答管线 CLI：python -X utf8 run.py --input questions.jsonl --output answers.jsonl"""
import re
import sqlite3
import time

import numpy as np

import llm
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
