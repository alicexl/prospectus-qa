"""招股书入库管线：解析→建库→embedding→实体链接表。CLI: python -X utf8 ingest.py"""
import re
from pathlib import Path

import fitz  # PyMuPDF
import pdfplumber

# ---------- 印刷页码 ----------
_PAGE_PATTERNS = [
    re.compile(r"第\s*([\d]{1,3}(?:-\d{1,3}){0,2})\s*页"),  # 第1-1-3页 / 第12页
    re.compile(r"^\s*(\d{1,3}-\d{1,3}-\d{1,4})\s*$"),        # 独立行 1-1-xx
    re.compile(r"^\s*(\d{1,4})\s*$"),                         # 独立行纯数字
]


def parse_printed_page(text: str) -> str | None:
    """逐行识别印刷页码（页码常是页尾独立行如 1-1-5，多行拼接会让 ^$ 锚失效）。"""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    candidates = lines[-3:] + lines[:2]  # 页尾优先，其次页首
    for line in reversed(candidates):
        for pat in _PAGE_PATTERNS:
            m = pat.search(line)
            if m:
                return m.group(1)
    return None


# ---------- 单 PDF 解析 ----------
def parse_pdf(pdf_path: str) -> dict:
    """PyMuPDF 文本 + pdfplumber 表格（bbox 剔除防重复），返回页块结构。"""
    doc_id = Path(pdf_path).stem
    pages = []
    with fitz.open(pdf_path) as doc, pdfplumber.open(pdf_path) as pl:
        for i, (page, plpage) in enumerate(zip(doc, pl.pages), start=1):
            tables = plpage.find_tables()
            table_bboxes = [t.bbox for t in tables]
            words = page.get_text("words")  # (x0,y0,x1,y1,word,block,line,word_no)

            def in_table(w):
                return any(b[0] - 2 <= w[0] and w[2] <= b[2] + 2
                           and b[1] - 2 <= w[1] and w[3] <= b[3] + 2
                           for b in table_bboxes)

            body_words = [w for w in words if not in_table(w)]
            body_words.sort(key=lambda w: (round(w[1], 1), w[0]))
            lines, cur, last_y = [], [], None
            for w in body_words:
                if last_y is not None and abs(w[1] - last_y) > 3:
                    lines.append(" ".join(cur))
                    cur = []
                cur.append(w[4])
                last_y = w[1]
            if cur:
                lines.append(" ".join(cur))
            text = "\n".join(lines)
            # 印刷页码：页首/页尾各取 2 行候选
            head = "\n".join(lines[:2])
            tail = "\n".join(lines[-2:])
            printed = parse_printed_page(head) or parse_printed_page(tail)
            pages.append({"pdf_page": i, "printed_page": printed,
                          "text": text, "tables": [t.extract() for t in tables]})
    _repair_printed_pages(pages)
    meta = extract_company_meta(pages)
    return {"doc_id": doc_id, "pages": pages,
            "company_name": meta[0], "stock_code": meta[1], "doc_type": meta[2]}


# ---------- 跨页表格合并 ----------
def _clean_rows(rows: list[list]) -> list[list]:
    """剔除全空行/全 None 行（pdfplumber 常见噪声）。"""
    return [[("" if c is None else c) for c in r] for r in rows
            if any(str(c or "").strip() for c in r)]


def _header_similar(a: list[list], b: list[list]) -> bool:
    """两个二维表的首行（表头）相似：列数一致且 ≥60% 单元格相同。"""
    if not a or not b or len(a[0]) != len(b[0]):
        return False
    same = sum(1 for x, y in zip(a[0], b[0]) if str(x or "").strip() == str(y or "").strip())
    return same / max(len(a[0]), 1) >= 0.6


def merge_cross_page_tables(raw_tables: list[dict]) -> list[dict]:
    """相邻页 + 表头相似（或页末/页首相接且同列数的无头续表）→ 并入前表。"""
    flat = []
    for p in raw_tables:
        tables = [c for c in (_clean_rows(t) for t in p["tables"] if t) if c]
        for i, rows in enumerate(tables):
            flat.append({"pdf_page": p["pdf_page"], "rows": rows,
                         "first_on_page": i == 0, "last_on_page": i == len(tables) - 1})
    merged: list[dict] = []
    for e in flat:
        prev = merged[-1] if merged else None
        adjacent = prev is not None and 0 <= e["pdf_page"] - prev["pdf_page"] <= 1
        if prev and adjacent and _header_similar(prev["rows"], e["rows"]):
            for r in e["rows"][1:]:  # 续页重复表头跳过
                if r not in prev["rows"]:
                    prev["rows"].append(r)
        elif (prev and adjacent and prev.get("last_on_page") and e["first_on_page"]
              and len(prev["rows"][0]) == len(e["rows"][0])
              and not _header_similar(prev["rows"], e["rows"])):
            prev["rows"].extend(e["rows"])  # 无重复表头的续表（数据行直接接上）
            prev["last_on_page"] = e["last_on_page"]
        else:
            merged.append(e)
    return merged


def table_to_text(rows: list[list]) -> str:
    """表格序列化参与检索：行内「、」连接，行间「 | 」。"""
    return " | ".join("、".join(str(c) if c is not None else "" for c in r) for r in rows)


# ---------- chunk 切分 ----------
_HEAD_RE = re.compile(
    r"^(第[一二三四五六七八九十百]+节|[一二三四五六七八九十]+、|（[一二三四五六七八九十]+）"
    r"|\d+(\.\d+)*[、．]|\d+(\.\d+)+\s)\s*\S")


def build_chunks(pages: list[dict], doc_id: str) -> list[dict]:
    """标题感知切分：标题行开启新 chunk；段落聚合 ≤500 字；表格整表一块。"""
    chunks: list[dict] = []
    for p in pages:
        buf: list[str] = []

        def flush():
            text = "\n".join(buf).strip()
            if text:
                chunks.append({"pdf_page": p["pdf_page"], "text": text})
            buf.clear()

        for line in p["text"].split("\n"):
            if _HEAD_RE.match(line.strip()) and buf:
                flush()
            buf.append(line)
            if sum(len(x) for x in buf) > 500:
                flush()
        flush()
        for t in p.get("tables", []):
            t = _clean_rows(t)
            if t:
                chunks.append({"pdf_page": p["pdf_page"], "text": "[表格]\n" + table_to_text(t)})
    return chunks


def _repair_printed_pages(pages: list[dict]) -> None:
    """全文档一致性修复：印刷页码主流格式族外的孤值（如封底孤行"3"）、
    同前缀组内非单调值 → 判为噪声置 None。支持 1-1-xx/1-2-xx 分节重编。"""
    from collections import Counter

    vals = [(p["pdf_page"], p["printed_page"]) for p in pages if p["printed_page"]]
    if len(vals) < 10:
        return
    family = lambda v: v.split("-")[0] if "-" in v else ""  # noqa: E731
    main_family, _ = Counter(family(v) for _, v in vals).most_common(1)[0]
    last_by_prefix: dict[str, int] = {}
    keep: dict[int, str] = {}
    for pg, v in vals:
        prefix = v.rsplit("-", 1)[0] if "-" in v else ""
        n = int(v.rsplit("-", 1)[-1])
        if main_family and family(v) != main_family:
            continue  # 异族孤值（正文页脚数字/封底编号）→ 置 None
        if prefix in last_by_prefix and n < last_by_prefix[prefix] - 1:
            continue  # 同组回退 → 置 None
        last_by_prefix[prefix] = n
        keep[pg] = v
    for p in pages:
        p["printed_page"] = keep.get(p["pdf_page"])


# ---------- 封面元数据（实体链接数据源） ----------
_RE_COMPANY = re.compile(r"([一-龥（）()]{4,30}(?:股份有限公司|有限责任公司|有限公司))")
_RE_CODE = re.compile(r"(?:股票代码|证券代码)[：:\s]*[（(]?(\d{6})[)）]?")
_RE_SHORT = re.compile(r"(?:公司简称|公司名称)[：:\s]*([一-龥A-Za-z0-9]{2,20})")


def extract_company_meta(pages: list[dict]) -> tuple[str, str, str]:
    """从前 20 页文本抽公司全称/股票代码（个别创业板文档公司名在第 16 页后才出现）。"""
    head_text = "\n".join(p["text"] for p in pages[:20])
    m = _RE_COMPANY.search(head_text)
    company = m.group(1) if m else ""
    c = _RE_CODE.search(head_text)
    code = c.group(1) if c else ""
    s = _RE_SHORT.search(head_text)
    short = s.group(1) if s else ""
    doc_type = "增发" if re.search(r"增发|非公开发行", head_text[:2000]) else "IPO"
    return company, code, doc_type


# ---------- 表格 chunk 构造（小表整片；超长表按行拆片，每片重复表头+章节引导句） ----------
_HEADING_LINE = re.compile(
    r"^(第[一二三四五六七八九十百]+节\s*.+|[一二三四五六七八九十]+、\S.*"
    r"|（[一二三四五六七八九十]+）\S.*|\d+(\.\d+)+\s?\S.*)$")


def _page_guides(pages: list[dict]) -> dict[int, str]:
    """page -> 该页结束时的当前标题行（节/小节标题，作表格引导句）。"""
    guides, cur = {}, ""
    for p in pages:
        for line in p["text"].split("\n"):
            s = line.strip()
            if len(s) <= 40 and _HEADING_LINE.match(s):
                cur = s
        guides[p["pdf_page"]] = cur
    return guides


def table_chunk_texts(pages: list[dict], merged_tables: list[dict],
                      max_chars: int = 1200, rows_per_piece: int = 50) -> list[dict]:
    """小表整表一片；超长表按行拆片（片内行列完整、每片重复表头行）；
    每片前拼章节引导句——超长合并表的 embedding 不再被全表平均稀释。"""
    guides = _page_guides(pages)
    out: list[dict] = []
    for mt in merged_tables:
        rows = mt["rows"]
        if not rows:
            continue
        header, body = rows[0], rows[1:]
        guide = guides.get(mt["pdf_page"], "")
        prefix = "[表格]" + (f"{guide}：" if guide else "")

        def piece(rs, start_page):
            return {"pdf_page": start_page,
                    "text": prefix + table_to_text([header] + rs)}

        if len(table_to_text(rows)) <= max_chars:
            out.append({"pdf_page": mt["pdf_page"], "text": prefix + table_to_text(rows)})
        else:
            for i in range(0, len(body), rows_per_piece):
                out.append(piece(body[i:i + rows_per_piece], mt["pdf_page"]))
    return out


# ---------- 建库 ----------
import json
import sqlite3

DB_PATH = str(Path(__file__).parent / "data" / "knowledge.db")


def get_conn(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS docs(
      doc_id TEXT PRIMARY KEY, company_name TEXT, stock_code TEXT,
      doc_type TEXT, page_count INTEGER);
    CREATE TABLE IF NOT EXISTS pages(
      doc_id TEXT, pdf_page INTEGER, printed_page TEXT, text TEXT,
      PRIMARY KEY(doc_id, pdf_page));
    CREATE TABLE IF NOT EXISTS blocks(
      doc_id TEXT, pdf_page INTEGER, block_id INTEGER, type TEXT,
      text TEXT, table_json TEXT);
    CREATE TABLE IF NOT EXISTS chunks(
      chunk_id INTEGER PRIMARY KEY AUTOINCREMENT, doc_id TEXT, pdf_page INTEGER,
      text TEXT, emb BLOB);
    CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(text, tokenize='trigram');
    CREATE TABLE IF NOT EXISTS company_registry(
      alias TEXT, doc_id TEXT, stock_code TEXT, PRIMARY KEY(alias, doc_id));
    CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(doc_id);
    """)


def doc_exists(conn: sqlite3.Connection, doc_id: str) -> bool:
    return conn.execute("SELECT 1 FROM docs WHERE doc_id=?", (doc_id,)).fetchone() is not None


def upsert_doc(conn, doc_id, company_name, stock_code, doc_type, page_count):
    conn.execute("INSERT OR REPLACE INTO docs VALUES (?,?,?,?,?)",
                 (doc_id, company_name, stock_code, doc_type, page_count))


# ---------- 单文档入库 ----------
def _write_doc(conn: sqlite3.Connection, parsed: dict) -> str:
    """写入单份解析结果。幂等：完整入库（docs+chunks 齐全）才跳过；残缺先清理重灌。
    单事务、成功才 commit，docs 行不会先于数据落库。"""
    doc_id = parsed["doc_id"]
    row = conn.execute(
        "SELECT (SELECT COUNT(*) FROM chunks WHERE chunks.doc_id=docs.doc_id)"
        " FROM docs WHERE doc_id=?", (doc_id,)).fetchone()
    if row and row[0] > 0:
        print(f"[skip] {doc_id} 已入库")
        return doc_id
    conn.execute("DELETE FROM chunks_fts WHERE rowid IN"
                 " (SELECT chunk_id FROM chunks WHERE doc_id=?)", (doc_id,))
    for tbl in ("chunks", "blocks", "pages", "docs", "company_registry"):
        conn.execute(f"DELETE FROM {tbl} WHERE doc_id=?", (doc_id,))
    upsert_doc(conn, doc_id, parsed["company_name"], parsed["stock_code"],
               parsed["doc_type"], len(parsed["pages"]))
    for p in parsed["pages"]:
        conn.execute("INSERT OR REPLACE INTO pages VALUES (?,?,?,?)",
                     (doc_id, p["pdf_page"], p["printed_page"], p["text"]))
    # 表格：跨页合并 → blocks(结构化JSON) + 整表chunk（起始页做溯源页）
    merged_tables = merge_cross_page_tables(parsed["pages"])
    for bi, mt in enumerate(merged_tables):
        conn.execute("INSERT INTO blocks VALUES (?,?,?,?,?,?)",
                     (doc_id, mt["pdf_page"], bi, "table",
                      table_to_text(mt["rows"]), json.dumps(mt["rows"], ensure_ascii=False)))
    # 文本 chunk：pages 去掉 tables（build_chunks 只切文本）
    text_pages = [{k: v for k, v in p.items() if k != "tables"} for p in parsed["pages"]]
    chunks = build_chunks(text_pages, doc_id)
    # 表格 chunk：小表整片、超长表按行拆片（带表头+章节引导句）
    chunks.extend(table_chunk_texts(parsed["pages"], merged_tables))
    for c in chunks:
        cur = conn.execute("INSERT INTO chunks(doc_id, pdf_page, text) VALUES (?,?,?)",
                           (doc_id, c["pdf_page"], c["text"]))
        conn.execute("INSERT INTO chunks_fts(rowid, text) VALUES (?,?)",
                     (cur.lastrowid, c["text"]))
    # 实体链接注册：全称 + 去后缀简称
    aliases = {parsed["company_name"]} if parsed["company_name"] else set()
    for suf in ("股份有限公司", "有限责任公司", "有限公司"):
        if parsed["company_name"].endswith(suf):
            aliases.add(parsed["company_name"][: -len(suf)])
    for a in aliases:
        if a:
            conn.execute("INSERT OR REPLACE INTO company_registry VALUES (?,?,?)",
                         (a, doc_id, parsed["stock_code"]))
    conn.commit()
    print(f"[ok] {doc_id} 公司={parsed['company_name']} 页数={len(parsed['pages'])} "
          f"表格={len(merged_tables)} chunks={len(chunks)}", flush=True)
    return doc_id


def ingest_pdf(conn: sqlite3.Connection, pdf_path: str, do_embed: bool = True) -> str:
    """单进程版：解析+写库（冒烟/测试用）。"""
    parsed = parse_pdf(pdf_path)
    doc_id = _write_doc(conn, parsed)
    if do_embed:
        _embed_doc_chunks(conn, doc_id)
    return doc_id


def _embed_doc_chunks(conn: sqlite3.Connection, doc_id: str) -> None:
    import numpy as np

    import llm
    rows = conn.execute(
        "SELECT chunk_id, text FROM chunks WHERE doc_id=? AND emb IS NULL", (doc_id,)).fetchall()
    if not rows:
        return
    vecs = llm.embed_parallel([r[1] for r in rows])
    for (cid, _), v in zip(rows, vecs):
        conn.execute("UPDATE chunks SET emb=? WHERE chunk_id=?",
                     (np.asarray(v, dtype=np.float32).tobytes(), cid))
    conn.commit()


# ---------- CLI ----------
if __name__ == "__main__":
    import argparse
    import glob as glob_mod
    from concurrent.futures import ProcessPoolExecutor, as_completed

    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf_dir", default="data/pdf")
    ap.add_argument("--workers", type=int, default=6, help="解析进程数")
    ap.add_argument("--embed-only", action="store_true", help="只为缺向量的chunk补embedding")
    args = ap.parse_args()
    Path("data").mkdir(exist_ok=True)
    conn = get_conn()
    init_db(conn)

    if args.embed_only:
        # 自测题相关公司优先（含"东微/国科微"别名的 doc 先补向量），其余按 doc_id 序
        pri = [r[0] for r in conn.execute(
            "SELECT DISTINCT doc_id FROM company_registry "
            "WHERE alias LIKE '%东微%' OR alias LIKE '%国科微%'")]
        rest = [r[0] for r in conn.execute(
            "SELECT DISTINCT doc_id FROM chunks WHERE emb IS NULL ORDER BY doc_id")]
        for d in [x for x in pri if x in rest] + [x for x in rest if x not in pri]:
            n = conn.execute("SELECT COUNT(*) FROM chunks WHERE doc_id=? AND emb IS NULL",
                             (d,)).fetchone()[0]
            if n == 0:
                continue
            print(f"[embed] {d} ({n} chunks)", flush=True)
            _embed_doc_chunks(conn, d)
        raise SystemExit(0)

    # 数据集扩展名大写 .PDF，双 pattern 兜底
    pdfs = sorted(set(glob_mod.glob(str(Path(args.pdf_dir) / "*.pdf")))
                  | set(glob_mod.glob(str(Path(args.pdf_dir) / "*.PDF"))))
    done = {r[0] for r in conn.execute(
        "SELECT doc_id FROM docs WHERE doc_id IN (SELECT DISTINCT doc_id FROM chunks)")}
    todo = [p for p in pdfs if Path(p).stem not in done]
    print(f"[info] 共 {len(pdfs)} 份，已完成 {len(done)}，待处理 {len(todo)}", flush=True)
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(parse_pdf, p): p for p in todo}
        for i, fut in enumerate(as_completed(futs), 1):
            p = futs[fut]
            try:
                _write_doc(conn, fut.result())
            except Exception as e:  # noqa: BLE001 单份失败不拖垮整批
                print(f"[FAIL] {Path(p).name}: {e}", flush=True)
            if i % 10 == 0:
                print(f"[progress] {i}/{len(todo)}", flush=True)


