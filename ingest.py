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
    """从页眉/页脚候选文本识别印刷页码；识别不到返回 None。"""
    for pat in _PAGE_PATTERNS:
        m = pat.search(text)
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
        tables = [_clean_rows(t) for t in p["tables"] if t]
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


# ---------- 封面元数据（实体链接数据源） ----------
_RE_COMPANY = re.compile(r"([一-龥（）()]{4,30}(?:股份有限公司|有限责任公司|有限公司))")
_RE_CODE = re.compile(r"(?:股票代码|证券代码)[：:\s]*[（(]?(\d{6})[)）]?")
_RE_SHORT = re.compile(r"(?:公司简称|公司名称)[：:\s]*([一-龥A-Za-z0-9]{2,20})")


def extract_company_meta(pages: list[dict]) -> tuple[str, str, str]:
    """从前 8 页文本抽公司全称/股票代码；doc_type 由关键词判定。"""
    head_text = "\n".join(p["text"] for p in pages[:8])
    m = _RE_COMPANY.search(head_text)
    company = m.group(1) if m else ""
    c = _RE_CODE.search(head_text)
    code = c.group(1) if c else ""
    s = _RE_SHORT.search(head_text)
    short = s.group(1) if s else ""
    doc_type = "增发" if re.search(r"增发|非公开发行", head_text[:2000]) else "IPO"
    return company, code, doc_type
