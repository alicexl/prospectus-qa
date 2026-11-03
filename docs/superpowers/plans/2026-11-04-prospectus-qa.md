# 招股书可溯源问答 Agent 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现题目二：80 份招股书 PDF + 1.46GB SQLite 的可溯源问答 Agent，P0 全项 + P1 按分值，deadline 2026-11-05 交付。

**Architecture:** 确定性管线 + LLM 节点内抽取。`ingest.py` 解析 PDF 建自包含 knowledge.db（FTS5 trigram + 向量 blob）；`run.py` 逐题：实体链接→路由→doc/sql 路→quote 程序化逐字校验→题目 §4 Schema 输出；`evaluate.py` 出 8 题五组指标。

**Tech Stack:** Python 3.12（Anaconda base）、PyMuPDF、pdfplumber、FTS5(trigram)、sqlglot、pydantic、openai SDK（DeepSeek 生成 + 智谱 embedding-3，均兼容端点）。

## Global Constraints

- 输出必须符合题目 §4 JSON Schema：`question_id/answer/answer_type(number|text|list|refusal)/value{number,unit}/items/citations[{doc_id,pdf_page,printed_page,quote}]/sql/route(doc|sql|hybrid|none)/confidence/latency_ms/tokens{input,output}`
- 引用 quote 必须能在对应页**逐字找到**（程序化校验保证，不靠 LLM 自觉）
- doc_id = PDF 文件名（去 .pdf 后缀的哈希值）
- API key 走环境变量：`DEEPSEEK_API_KEY`、`ZHIPU_API_KEY`（智谱 key 格式 `id.secret`），代码零硬编码
- 数据在 `data/`（gitignore）；knowledge.db 放 `data/knowledge.db`（可重建，不进 git）
- LLM 不做任何心算——数值一律确定性工具执行
- CLI 幂等：ingest 已入库 doc 跳过；run 逐行写输出，单题失败重试 3 次后输出 refusal+confidence=0，不中断整批
- 文件 IO 全部显式 `encoding="utf-8"`；Windows GBK 环境入口 `python -X utf8`
- commit message：中文 + Conventional Commits 前缀
- 文件结构（CLAUDE.md 单调用方原则）：`llm.py`（ingest/run 共用）、`schema.py`（run/evaluate 共用）、`ingest.py`/`run.py`/`evaluate.py` 三个用户场景 CLI，其余逻辑内聚各 CLI

---

### Task 0: 依赖与基础设施（llm.py + schema.py）

**Files:**
- Create: `requirements.txt`
- Create: `llm.py`
- Create: `schema.py`
- Test: `tests/test_schema.py`

**Interfaces:**
- Produces: `llm.chat(system, user, model="deepseek-chat", temperature=0.0) -> tuple[str, dict]`（content, usage{input,output}）；`llm.embed(texts: list[str]) -> list[list[float]]`（智谱 embedding-3）；`schema.AnswerRecord`（pydantic，题目 §4 全字段）、`schema.Value`、`schema.Citation`

- [ ] **Step 1: 安装依赖 + requirements.txt**

```bash
pip install pdfplumber sqlglot
```
requirements.txt：
```
pymupdf
pdfplumber
sqlglot
pydantic
openai
```
（pymupdf/pydantic/openai base 环境已有则不重装，requirements 记录全量。）

- [ ] **Step 2: 写 schema.py（先写测试）**

tests/test_schema.py：
```python
from schema import AnswerRecord, Citation, Value

def test_number_record_roundtrip():
    r = AnswerRecord(
        question_id="q1", answer="发行价 12.50 元/股", answer_type="number",
        value=Value(number=12.50, unit="元"),
        citations=[Citation(doc_id="abc123", pdf_page=3, printed_page="1-1-3",
                            quote="发行价格为12.50元/股")],
        route="doc", confidence=0.9, latency_ms=1200, tokens={"input": 800, "output": 100},
    )
    d = r.model_dump()
    assert d["value"]["unit"] == "元" and d["citations"][0]["pdf_page"] == 3

def test_refusal_defaults():
    r = AnswerRecord(question_id="q2", answer="知识库中不存在该公司", answer_type="refusal", route="none")
    d = r.model_dump()
    assert d["value"]["number"] is None and d["items"] == [] and d["sql"] is None and d["tokens"] == {"input": 0, "output": 0}
```

- [ ] **Step 3: 跑测试验证失败**

Run: `python -X utf8 -m pytest tests/test_schema.py -v`
Expected: FAIL（No module named 'schema'）

- [ ] **Step 4: 写 schema.py**

```python
"""题目§4输出Schema——pydantic严格校验。run 产出、evaluate 消费。"""
from typing import Literal
from pydantic import BaseModel, Field

UNIT = Literal["元", "万元", "亿元", "%", "股", None]

class Value(BaseModel):
    number: float | None = None
    unit: UNIT = None

class Citation(BaseModel):
    doc_id: str
    pdf_page: int
    printed_page: str | None = None
    quote: str

class AnswerRecord(BaseModel):
    question_id: str
    answer: str
    answer_type: Literal["number", "text", "list", "refusal"]
    value: Value = Field(default_factory=Value)
    items: list[str] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    sql: str | None = None
    route: Literal["doc", "sql", "hybrid", "none"] = "none"
    confidence: float = 0.0
    latency_ms: int = 0
    tokens: dict[str, int] = Field(default_factory=lambda: {"input": 0, "output": 0})
```

- [ ] **Step 5: 跑测试通过**

Run: `python -X utf8 -m pytest tests/test_schema.py -v`
Expected: 2 passed

- [ ] **Step 6: 写 llm.py**

```python
"""DeepSeek 生成 + 智谱 embedding-3，均走 openai 兼容 SDK。key 只从环境变量取。"""
import os
import time
from openai import OpenAI

DEEPSEEK_BASE = "https://api.deepseek.com"
ZHIPU_BASE = "https://open.bigmodel.cn/api/paas/v4/"

def _deepseek() -> OpenAI:
    return OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"], base_url=DEEPSEEK_BASE)

def _zhipu() -> OpenAI:
    return OpenAI(api_key=os.environ["ZHIPU_API_KEY"], base_url=ZHIPU_BASE)

def chat(system: str, user: str, model: str = "deepseek-chat",
         temperature: float = 0.0, retries: int = 3) -> tuple[str, dict]:
    """返回 (content, usage)。usage 取 prompt_tokens/completion_tokens。"""
    last_err = None
    for i in range(retries):
        try:
            resp = _deepseek().chat.completions.create(
                model=model, temperature=temperature,
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": user}])
            u = resp.usage
            return resp.choices[0].message.content, {"input": u.prompt_tokens, "output": u.completion_tokens}
        except Exception as e:  # noqa: BLE001 限流/网络退避重试
            last_err = e
            time.sleep(2 ** i)
    raise RuntimeError(f"chat failed after {retries} retries") from last_err

def embed(texts: list[str]) -> list[list[float]]:
    """智谱 embedding-3，分批 64，返回与输入等长向量列表。"""
    out: list[list[float]] = []
    for i in range(0, len(texts), 64):
        batch = texts[i:i + 64]
        for attempt in range(3):
            try:
                resp = _zhipu().embeddings.create(model="embedding-3", input=batch)
                out.extend(d.embedding for d in resp.data)
                break
            except Exception:  # noqa: BLE001
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)
    return out
```

- [ ] **Step 7: 确认两个 key 在环境（缺则向用户要，本步骤不阻塞后续解析类任务）**

Run: `python -c "import os; print(bool(os.environ.get('DEEPSEEK_API_KEY')), bool(os.environ.get('ZHIPU_API_KEY')))"`
Expected: `True True`（False 的项向用户索取）

- [ ] **Step 8: Commit**

```bash
git add requirements.txt llm.py schema.py tests/test_schema.py
git commit -m "feat: 基础设施——llm封装(deepseek生成+智谱embedding)与题目§4输出Schema"
```

---

### Task 1: PDF 解析核心——单 PDF → 页块结构（ingest.py 第一部分）

**Files:**
- Create: `ingest.py`
- Test: `tests/test_parse.py`

**Interfaces:**
- Produces: `ingest.parse_printed_page(header_footer_text: str) -> str | None`（印刷页码，支持 `1-1-xx`）；`ingest.parse_pdf(pdf_path: str) -> dict`（`{"doc_id", "pages": [{"pdf_page", "printed_page", "text", "tables": [[...]]}], "company_name", "stock_code", "doc_type"}`）；`ingest.extract_company_meta(pages: list[dict]) -> tuple[str, str, str]`

- [ ] **Step 1: 写纯函数单测（不依赖 PDF 文件）**

tests/test_parse.py：
```python
from ingest import parse_printed_page

def test_printed_page_patterns():
    assert parse_printed_page("第 1-1-3 页") == "1-1-3"
    assert parse_printed_page("第一节 释义 第1-1-15页") == "1-1-15"
    assert parse_printed_page("第 12 页 共 300 页") == "12"
    assert parse_printed_page("1-2-8") == "1-2-8"
    assert parse_printed_page("17") == "17"
    assert parse_printed_page("风险因素提示") is None
    assert parse_printed_page("公司拟公开发行股票") is None
```

- [ ] **Step 2: 跑测试验证失败**

Run: `python -X utf8 -m pytest tests/test_parse.py -v`
Expected: FAIL（cannot import 'parse_printed_page'）

- [ ] **Step 3: 写 ingest.py 解析部分**

```python
"""招股书入库管线：解析→建库→embedding→实体链接表。CLI: python -X utf8 ingest.py"""
import re
import sys
from pathlib import Path

import fitz  # PyMuPDF
import pdfplumber

# ---------- 印刷页码 ----------
_PAGE_PATTERNS = [
    re.compile(r"第\s*([\d]{1,3}(?:-\d{1,3}){0,2})\s*页"),  # 第1-1-3页 / 第12页
    re.compile(r"^\s*(\d{1,3}-\d{1,3}-\d{1,4})\s*$"),        # 独立行 1-1-xx
    re.compile(r"^\s*(\d{1,4})\s*$"),                          # 独立行纯数字
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
            words = page.get_text("words")  # (x0,y0,x1,y1,word,...)
            table_bboxes = [t.bbox for t in plpage.find_tables()]
            def in_table(w):
                return any(b[0] - 2 <= w[0] and w[2] <= b[2] + 2 and b[1] - 2 <= w[1] and w[3] <= b[3] + 2 for b in table_bboxes)
            body_words = [w for w in words if not in_table(w)]
            # 按 y 分行聚合文本
            body_words.sort(key=lambda w: (round(w[1], 1), w[0]))
            lines, cur, last_y = [], [], None
            for w in body_words:
                if last_y is not None and abs(w[1] - last_y) > 3:
                    lines.append(" ".join(cur)); cur = []
                cur.append(w[4]); last_y = w[1]
            if cur:
                lines.append(" ".join(cur))
            text = "\n".join(lines)
            # 印刷页码：页首/页尾各取 2 行候选
            head = "\n".join(lines[:2]); tail = "\n".join(lines[-2:])
            printed = parse_printed_page(head) or parse_printed_page(tail)
            tables = [t.extract() for t in plpage.find_tables()]
            pages.append({"pdf_page": i, "printed_page": printed,
                          "text": text, "tables": tables})
    meta = extract_company_meta(pages)
    return {"doc_id": doc_id, "pages": pages,
            "company_name": meta[0], "stock_code": meta[1], "doc_type": meta[2]}

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
    doc_type = "增发" if re.search(r"增发|非公开发行", head_text[:2000]) else "IPO"
    return company, code, doc_type
```

- [ ] **Step 4: 跑测试通过**

Run: `python -X utf8 -m pytest tests/test_parse.py -v`
Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add ingest.py tests/test_parse.py
git commit -m "feat: PDF解析核心——文本/表格bbox剔除/印刷页码1-1-xx识别/封面公司元数据"
```

---

### Task 2: 跨页表格合并 + chunk 切分（纯函数）

**Files:**
- Modify: `ingest.py`（追加函数）
- Test: `tests/test_chunk.py`

**Interfaces:**
- Produces: `ingest.merge_cross_page_tables(raw_tables: list[dict]) -> list[dict]`（输入 `{"pdf_page", "tables": [[...]]}` 按页序列，输出合并后 `{"pdf_page", "rows": [[...]]}`）；`ingest.table_to_text(rows: list[list]) -> str`；`ingest.build_chunks(pages: list[dict], doc_id: str) -> list[dict]`（`{"pdf_page", "text"}`，标题感知 + 表格整块）

- [ ] **Step 1: 写单测**

tests/test_chunk.py：
```python
from ingest import merge_cross_page_tables, table_to_text, build_chunks

def _raw():
    t1 = [["项目", "金额"], ["募集资金总额", "50,000"], ["补充流动资金", "10,000"]]
    t2 = [["项目", "金额"], ["研发中心", "20,000"]]  # 同表头续页
    t3 = [["年份", "营收"], ["2016", "30,000"]]      # 不同表，不合并
    return [{"pdf_page": 10, "tables": [t1]},
            {"pdf_page": 11, "tables": [t2, t3]}]

def test_merge_same_header():
    merged = merge_cross_page_tables(_raw())
    assert len(merged) == 2
    m0 = [m for m in merged if m["pdf_page"] == 10][0]
    assert m0["rows"][0] == ["项目", "金额"]
    assert ["研发中心", "20,000"] in m0["rows"]  # 续页数据并入
    assert m0["rows"].count(["项目", "金额"]) == 1  # 续页表头去重

def test_table_to_text():
    txt = table_to_text([["项目", "金额"], ["总额", "5亿"]])
    assert "项目" in txt and "总额" in txt and "5亿" in txt

def test_build_chunks_keeps_table_whole_and_page():
    pages = [{"pdf_page": 3, "printed_page": "1-1-3",
              "text": "募集资金运用\n本次发行募集资金总额为50,000万元。",
              "tables": [[["项目", "金额"], ["总额", "50,000"]]]}]
    chunks = build_chunks(pages, "doc1")
    assert all(c["pdf_page"] == 3 for c in chunks)
    joined = "\n".join(c["text"] for c in chunks)
    assert "50,000" in joined
```

- [ ] **Step 2: 跑测试验证失败**

Run: `python -X utf8 -m pytest tests/test_chunk.py -v`
Expected: FAIL（import error）

- [ ] **Step 3: 实现（追加到 ingest.py）**

```python
# ---------- 跨页表格合并 ----------
def _header_similar(a: list[list], b: list[list]) -> bool:
    if not a or not b or len(a[0]) != len(b[0]):
        return False
    same = sum(1 for x, y in zip(a[0], b[0]) if (x or "").strip() == (y or "").strip())
    return same / max(len(a[0]), 1) >= 0.6

def merge_cross_page_tables(raw_tables: list[dict]) -> list[dict]:
    """相邻页、列数一致、表头相似 → 后页数据行并入前页表（去重表头）。"""
    flat = [(p["pdf_page"], i, t)
            for p in raw_tables for i, t in enumerate(p["tables"]) if t]
    merged: list[dict] = []
    for pdf_page, _ti, rows in flat:
        if (merged and pdf_page - merged[-1]["pdf_page"] <= 1
                and _header_similar(merged[-1]["rows"], [rows])):
            for r in rows[1:] if _header_similar([rows], merged[-1]["rows"]) else rows:
                if r not in merged[-1]["rows"]:
                    merged[-1]["rows"].append(r)
        else:
            merged.append({"pdf_page": pdf_page, "rows": [list(r) for r in rows]})
    return merged

def table_to_text(rows: list[list]) -> str:
    """表格序列化参与检索：行内"、"连接，行间" | "。None 单元格转空串。"""
    return " | ".join("、".join(str(c) if c is not None else "" for c in r) for r in rows)

# ---------- chunk 切分 ----------
_HEAD_RE = re.compile(r"^(第[一二三四五六七八九十百]+节|[一二三四五六七八九十]+、|\d+(\.\d+)*[、．.])\s*\S")

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
            if t:
                chunks.append({"pdf_page": p["pdf_page"], "text": "[表格]\n" + table_to_text(t)})
    return chunks
```

- [ ] **Step 4: 跑测试通过**

Run: `python -X utf8 -m pytest tests/test_chunk.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add ingest.py tests/test_chunk.py
git commit -m "feat: 跨页表格合并(表头相似判定)+表格序列化+标题感知chunk切分"
```

---

### Task 3: 建库 + embedding + 全量入库 CLI（幂等）

**Files:**
- Modify: `ingest.py`（追加建库与 CLI）
- Test: `tests/test_db.py`（内存库建表+断点续跑）

**Interfaces:**
- Produces: `ingest.DB_PATH = "data/knowledge.db"`；`ingest.init_db(conn)`；`ingest.ingest_pdf(conn, pdf_path, skip_embed=False)`（幂等：doc 已存在跳过）；CLI `python -X utf8 ingest.py [--pdf_dir data/pdf] [--no-embed]`；表结构 docs/pages/blocks/chunks(+FTS5 trigram)/company_registry，见 spec §4

- [ ] **Step 1: 写单测（内存 SQLite）**

tests/test_db.py：
```python
import sqlite3
from ingest import init_db, upsert_doc, doc_exists

def test_init_and_idempotent():
    conn = sqlite3.connect(":memory:")
    init_db(conn)
    upsert_doc(conn, doc_id="abc", company_name="苏州东微半导体股份有限公司",
               stock_code="688261", doc_type="IPO", page_count=10)
    assert doc_exists(conn, "abc") is True
    assert doc_exists(conn, "nope") is False
    # FTS5 trigram 可用性
    conn.execute("INSERT INTO chunks_fts(rowid, text) VALUES (1, '募集资金总额为50,000万元')")
    hit = conn.execute("SELECT text FROM chunks_fts WHERE chunks_fts MATCH '募集资金'").fetchall()
    assert len(hit) == 1
```

- [ ] **Step 2: 验证失败 → Step 3 实现建库层**

追加到 ingest.py：
```python
# ---------- 建库 ----------
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
    conn.commit()
```

- [ ] **Step 4: 跑测试通过**

Run: `python -X utf8 -m pytest tests/test_db.py -v`
Expected: 1 passed

- [ ] **Step 5: 实现 ingest_pdf 主流程 + CLI（追加）**

```python
# ---------- 单文档入库 ----------
def ingest_pdf(conn: sqlite3.Connection, pdf_path: str, do_embed: bool = True) -> str:
    doc_id = Path(pdf_path).stem
    if doc_exists(conn, doc_id):
        print(f"[skip] {doc_id} 已入库")
        return doc_id
    parsed = parse_pdf(pdf_path)
    upsert_doc(conn, doc_id, parsed["company_name"], parsed["stock_code"],
               parsed["doc_type"], len(parsed["pages"]))
    for p in parsed["pages"]:
        conn.execute("INSERT OR REPLACE INTO pages VALUES (?,?,?,?)",
                     (doc_id, p["pdf_page"], p["printed_page"], p["text"]))
        for bi, t in enumerate(p["tables"]):
            if t:
                conn.execute("INSERT INTO blocks VALUES (?,?,?,?,?,?)",
                             (doc_id, p["pdf_page"], bi, "table",
                              table_to_text(t), json.dumps(t, ensure_ascii=False)))
    chunks = build_chunks(parsed["pages"], doc_id)
    for c in chunks:
        cur = conn.execute("INSERT INTO chunks(doc_id, pdf_page, text) VALUES (?,?,?)",
                           (doc_id, c["pdf_page"], c["text"]))
        conn.execute("INSERT INTO chunks_fts(rowid, text) VALUES (?,?)",
                     (cur.lastrowid, c["text"]))
    # 实体链接注册：全称 + 简称（公司名去"股份有限公司"等后缀的前缀段）
    aliases = {parsed["company_name"]} if parsed["company_name"] else set()
    for suf in ("股份有限公司", "有限责任公司", "有限公司"):
        if parsed["company_name"].endswith(suf):
            aliases.add(parsed["company_name"][: -len(suf)])
    for a in aliases:
        if a:
            conn.execute("INSERT OR REPLACE INTO company_registry VALUES (?,?,?)",
                         (a, doc_id, parsed["stock_code"]))
    conn.commit()
    if do_embed:
        _embed_doc_chunks(conn, doc_id)
    return doc_id

def _embed_doc_chunks(conn: sqlite3.Connection, doc_id: str) -> None:
    import llm
    rows = conn.execute(
        "SELECT chunk_id, text FROM chunks WHERE doc_id=? AND emb IS NULL", (doc_id,)).fetchall()
    if not rows:
        return
    vecs = llm.embed([r[1] for r in rows])
    for (cid, _), v in zip(rows, vecs):
        conn.execute("UPDATE chunks SET emb=? WHERE chunk_id=?",
                     (np.asarray(v, dtype=np.float32).tobytes(), cid))
    conn.commit()

# ---------- CLI ----------
if __name__ == "__main__":
    import argparse, glob as _glob
    import json as json  # noqa 已在上方 import
    import numpy as np
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf_dir", default="data/pdf")
    ap.add_argument("--no-embed", action="store_true")
    args = ap.parse_args()
    Path("data").mkdir(exist_ok=True)
    conn = get_conn()
    init_db(conn)
    pdfs = sorted(p for p in _glob.glob(str(Path(args.pdf_dir) / "*.pdf")))
    print(f"[info] 共 {len(pdfs)} 份 PDF")
    for i, p in enumerate(pdfs, 1):
        print(f"[{i}/{len(pdfs)}] {Path(p).name}")
        ingest_pdf(conn, p, do_embed=not args.no_embed)
```

（实现时把 `import json`、`import numpy as np` 挪到文件顶部，上面 CLI 段保持整洁。）

- [ ] **Step 6: 下载数据集（~2GB，后台）**

```bash
pip install modelscope
modelscope download --dataset BJQW14Bbs_challenge_financial_14b_dataset --local_dir data/
```
Expected: `data/pdf/` 80 份哈希名 PDF、`data/pdf_txt_file/`、`data/dataset/博金杯比赛数据.db`、`data/question.json`

- [ ] **Step 7: 冒烟——1 份真实 PDF 全链路（先 --no-embed 验证解析，再补 embed）**

Run: `python -X utf8 -c "from ingest import *; c=get_conn(); init_db(c); import glob; p=sorted(glob.glob('data/pdf/*.pdf'))[0]; ingest_pdf(c, p, do_embed=False)"` 然后 SQLite 抽查该 doc 的 pages/chunks 行数、printed_page 非空率、表格 blocks 存在。
Expected: 无异常；printed_page 识别率 > 60%（否则回改 `_PAGE_PATTERNS` 再跑）

- [ ] **Step 8: 全量 80 份入库（后台跑，预计 30–90 分钟）**

Run: `python -X utf8 ingest.py`
Expected: 80 份全部 ingest，chunks 表行数 > 5 万；company_registry 覆盖 80 doc

- [ ] **Step 9: 抽检 20 页人工比对（打印页文本 + 原 PDF 对照）**

Run: `python -X utf8 -c "from ingest import *; c=get_conn(); rows=c.execute('SELECT doc_id,pdf_page,text FROM pages ORDER BY RANDOM() LIMIT 20').fetchall(); [print(r[0], r[1], r[2][:200], '\n---') for r in rows]"`
人工抽查：文本完整、无表格重复混入、页码正确。

- [ ] **Step 10: Commit**

```bash
git add ingest.py tests/test_db.py
git commit -m "feat: 建库(embedding/FTS5/实体链接注册)+全量入库CLI幂等断点续跑"
```

---

### Task 4: 检索 + 实体链接查询 + 路由（run.py 第一部分）

**Files:**
- Create: `run.py`
- Test: `tests/test_retrieve.py`

**Interfaces:**
- Consumes: `ingest.get_conn/init_db/DB_PATH`、`llm.embed`
- Produces: `run.search(conn, query, doc_id=None, k=8) -> list[dict]`（chunk 行 + rrf_score，含 pdf_page/text）；`run.link_company(conn, question) -> str | None`（doc_id）；`run.route(conn, question, doc_id) -> str`（doc/sql/hybrid/none 规则版）

- [ ] **Step 1: 写单测（内存库造数据）**

tests/test_retrieve.py：
```python
import sqlite3
import numpy as np
from ingest import init_db
from run import link_company, route, rrf, search

def _conn():
    c = sqlite3.connect(":memory:"); init_db(c); return c

def test_link_company_longest_match():
    c = _conn()
    c.execute("INSERT INTO company_registry VALUES ('苏州东微半导体股份有限公司','d1','688261')")
    c.execute("INSERT INTO company_registry VALUES ('苏州东微半导体','d1','688261')")
    c.execute("INSERT INTO company_registry VALUES ('湖南国科微电子股份有限公司','d2','300672')")
    assert link_company(c, "苏州东微半导体股份有限公司本次公开发行股数是多少？") == "d1"
    assert link_company(c, "湖南国科微电子 2016 年营业收入是多少？") == "d2"
    assert link_company(c, "丽岛新材料本次IPO预计募集资金总额是多少？") is None

def test_route_rules():
    c = _conn()
    assert route(c, "列出招股书中披露的全部风险因素", "d1") == "doc"
    assert route(c, "东微半导体本次募集资金投资项目合计多少？", "d1") == "doc"
    assert route(c, "丽岛新材料本次IPO预计募集资金总额是多少？", None) == "none"
    # 无 doc_id 但含 DB 关键词 → sql；两者都涉及 → hybrid
    assert route(c, "某基金2020年持仓了哪些股票？", None) == "sql"
    assert route(c, "国科微2016年营收多少？基金持仓多少？", "d2") == "hybrid"

def test_rrf():
    assert rrf([["a"], ["b"]], [["b"], ["a"]])["a"] == rrf([["a"], ["b"]], [["b"], ["a"]])["b"]
    top = max(rrf([["x"], ["y"]], [["x"], ["z"]]).items(), key=lambda kv: kv[1])[0]
    assert top == "x"
```

- [ ] **Step 2: 验证失败 → Step 3 实现**

run.py：
```python
"""问答管线 CLI：python -X utf8 run.py --input questions.jsonl --output answers.jsonl"""
import json
import re
import sqlite3
import time
from pathlib import Path

import numpy as np

import llm
from ingest import DB_PATH, get_conn, init_db

# ---------- RRF 融合 ----------
def rrf(*ranked_lists, k: int = 60) -> dict:
    """多路排序列表 → {item: score}，score=Σ1/(k+rank)。"""
    scores: dict = {}
    for lst in ranked_lists:
        for rank, item in enumerate(lst, start=1):
            key = item[0] if isinstance(item, (list, tuple)) else item
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
    return scores

# ---------- 实体链接 ----------
def link_company(conn: sqlite3.Connection, question: str) -> str | None:
    """公司词典最长匹配 → doc_id。匹配不到=知识库外 → None。"""
    rows = conn.execute("SELECT alias, doc_id FROM company_registry").fetchall()
    best_len, best_doc = 0, None
    for alias, doc_id in rows:
        if alias in question and len(alias) > best_len:
            best_len, best_doc = len(alias), doc_id
    return best_doc

# ---------- 路由（规则优先，LLM 兜底在 Task 5 接入） ----------
_SQL_HINT = re.compile(r"基金|持仓|行情|份额|规模变动|持有人结构|日行情|涨跌幅")
_DOC_HINT = re.compile(r"招股书|披露|募集|风险因素|发行股数|发行价格|营业收入|主营业务|股东|承诺")

def route(conn: sqlite3.Connection, question: str, doc_id: str | None) -> str:
    if doc_id is None:
        return "sql" if _SQL_HINT.search(question) else "none"
    if _SQL_HINT.search(question) and (_DOC_HINT.search(question) or re.search(r"20\d\d", question)):
        return "hybrid"
    return "doc"

# ---------- 混合检索 ----------
def _cos(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return float(a @ b / (na * nb)) if na and nb else 0.0

def search(conn: sqlite3.Connection, query: str, doc_id: str | None = None, k: int = 8) -> list[dict]:
    """BM25(FTS5 trigram) + 向量余弦 → RRF top-k。返回 chunk 行(含 pdf_page/text/rrf_score)。"""
    where, params = "", []
    if doc_id:
        where = "AND c.doc_id=?"; params = [doc_id]
    bm = conn.execute(
        f"""SELECT c.chunk_id, c.doc_id, c.pdf_page, c.text FROM chunks_fts f
            JOIN chunks c ON c.rowid=f.rowid
            WHERE chunks_fts MATCH ? {"" if not doc_id else "AND c.doc_id=?"}
            ORDER BY rank LIMIT 30""",
        [query[:200]] + params).fetchall()
    qvec = np.asarray(llm.embed([query])[0], dtype=np.float32)
    rows = conn.execute(
        f"SELECT chunk_id, doc_id, pdf_page, text, emb FROM chunks "
        f"{'WHERE doc_id=?' if doc_id else ''}", params).fetchall()
    vecs = [(r[0], _cos(qvec, np.frombuffer(r[4], dtype=np.float32))) for r in rows if r[4]]
    vecs.sort(key=lambda x: -x[1])
    bm_ids = [(r[0],) for r in bm]
    vec_ids = [(i,) for i, _ in vecs[:30]]
    scores = rrf(bm_ids, vec_ids)
    by_id = {r[0]: r for r in rows}
    top = sorted(scores.items(), key=lambda kv: -kv[1])[:k]
    return [{"chunk_id": cid, "doc_id": by_id[cid][1], "pdf_page": by_id[cid][2],
             "text": by_id[cid][3], "rrf_score": s} for cid, s in top if cid in by_id]
```

- [ ] **Step 4: 跑测试通过**

Run: `python -X utf8 -m pytest tests/test_retrieve.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add run.py tests/test_retrieve.py
git commit -m "feat: 实体链接最长匹配+规则路由+BM25/向量RRF混合检索"
```

---

### Task 5: doc 路——生成 + quote 逐字校验 + 拒答 + CLI 主循环（P0 闭环）

**Files:**
- Modify: `run.py`（追加）
- Test: `tests/test_verify.py`

**Interfaces:**
- Consumes: `run.search/link_company/route`、`llm.chat`、`schema.AnswerRecord`
- Produces: `run.norm_text(s) -> str`（去空白+全半角规范化）；`run.verify_quote(conn, citation) -> bool`；`run.answer_doc(conn, question_id, question, doc_id) -> AnswerRecord`；CLI 主循环 `main()`

- [ ] **Step 1: 写 quote 校验单测**

tests/test_verify.py：
```python
from run import norm_text, verify_quote
from ingest import init_db
import sqlite3

def test_norm_text():
    assert norm_text("募集 资金\n总额") == norm_text("募集资金总额")
    assert norm_text("５０００万元") == norm_text("5000万元")  # 全角数字
    assert norm_text("（元）") == norm_text("(元)")           # 全角括号

def test_verify_quote_on_page():
    c = sqlite3.connect(":memory:"); init_db(c)
    c.execute("INSERT INTO pages VALUES ('d1', 3, '1-1-3', '本次发行募集资金总额为 50,000 万元。')")
    ok = verify_quote(c, {"doc_id": "d1", "pdf_page": 3, "quote": "募集资金总额为 50,000 万元"})
    bad_page = verify_quote(c, {"doc_id": "d1", "pdf_page": 4, "quote": "募集资金总额"})
    bad_text = verify_quote(c, {"doc_id": "d1", "pdf_page": 3, "quote": "不存在的文字"})
    assert ok and not bad_page and not bad_text
```

- [ ] **Step 2: 验证失败 → Step 3 实现（追加到 run.py）**

```python
# ---------- quote 程序化逐字校验 ----------
_FULL2HALF = str.maketrans("０１２３４５６７８９（）　：，。", "0123456789() :，.")

def norm_text(s: str) -> str:
    """规范化：全角→半角、去全部空白。quote 逐字匹配在此空间进行。"""
    return re.sub(r"\s+", "", s.translate(_FULL2HALF))

def verify_quote(conn: sqlite3.Connection, cite: dict) -> bool:
    row = conn.execute("SELECT text FROM pages WHERE doc_id=? AND pdf_page=?",
                       (cite["doc_id"], cite["pdf_page"])).fetchone()
    return bool(row) and norm_text(cite["quote"]) in norm_text(row[0])

# ---------- doc 路生成 ----------
_DOC_SYSTEM = """你是招股书问答助手。仅依据给出的资料片段回答，答案与引用必须逐字来自原文。
输出 JSON：{"answer": str, "answer_type": "number|text|list|refusal", "value": {"number": float|null, "unit": "元|万元|亿元|%|股|null"}, "items": [str], "citations": [{"pdf_page": int, "quote": str}], "confidence": 0-1}
规则：数值只抄原文数字不要心算；信息在片段中不存在则 answer_type=refusal 并在 answer 说明；引用 quote 必须是原文连续片段（≤80字）。"""

def answer_doc(conn, question_id: str, question: str, doc_id: str) -> "AnswerRecord":
    import schema
    chunks = search(conn, question, doc_id=doc_id, k=8)
    ctx = "\n\n".join(f"[片段 pdf_page={c['pdf_page']}]\n{c['text']}" for c in chunks)
    content, usage = llm.chat(_DOC_SYSTEM, f"问题：{question}\n\n资料：\n{ctx}")
    m = re.search(r"\{.*\}", content, re.S)
    data = json.loads(m.group(0)) if m else {}
    # 检索置信不足 → 拒答
    top_score = chunks[0]["rrf_score"] if chunks else 0.0
    at = data.get("answer_type", "refusal")
    if not chunks or (top_score < 0.016 and at != "refusal"):
        at, data["answer"] = "refusal", "检索置信不足，知识库中未找到充分依据"
    cites = []
    for ct in data.get("citations", []):
        cand = {"doc_id": doc_id, "pdf_page": ct.get("pdf_page", 0), "quote": ct.get("quote", "")}
        if verify_quote(conn, cand):           # 程序化逐字校验，失败即弃
            pr = conn.execute("SELECT printed_page FROM pages WHERE doc_id=? AND pdf_page=?",
                              (doc_id, cand["pdf_page"])).fetchone()
            cites.append({**cand, "printed_page": pr[0] if pr else None})
    rec = schema.AnswerRecord(
        question_id=question_id,
        answer=data.get("answer", ""), answer_type=at,
        value=schema.Value(**data.get("value", {}) or {}),
        items=data.get("items") or [], citations=[schema.Citation(**c) for c in cites],
        route="doc", confidence=float(data.get("confidence", 0.5)),
        tokens=usage)
    if at != "refusal" and not cites:          # 有答案但引用全被校验毙掉 → 降级拒答
        rec.answer_type, rec.answer, rec.confidence = "refusal", "引用无法在原文逐字验证，拒答", 0.0
    return rec

# ---------- CLI 主循环 ----------
def refuse(question_id: str, question: str, reason: str, route_v: str = "none") -> "AnswerRecord":
    import schema
    return schema.AnswerRecord(question_id=question_id, answer=reason,
                               answer_type="refusal", route=route_v, confidence=0.0)

def answer_one(conn, qid: str, question: str) -> "AnswerRecord":
    t0 = time.time()
    try:
        doc_id = link_company(conn, question)
        if doc_id is None:
            rec = refuse(qid, question, "知识库中不存在该公司（80份招股书未覆盖）", "none")
        else:
            r = route(conn, question, doc_id)
            rec = {"doc": lambda: answer_doc(conn, qid, question, doc_id),
                   "sql": lambda: answer_sql(conn, qid, question, doc_id),
                   "hybrid": lambda: answer_hybrid(conn, qid, question, doc_id),
                   "none": lambda: refuse(qid, question, "无法路由", "none")}[r]()
    except Exception as e:  # noqa: BLE001 单题失败不中断整批
        rec = refuse(qid, question, f"处理失败：{e}")
    rec.latency_ms = int((time.time() - t0) * 1000)
    return rec

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    conn = get_conn(); init_db(conn)
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
```

（`answer_sql/answer_hybrid` Task 7 补；本任务先放占位抛异常函数名引用错误没关系——不，**不能占位**：本任务先在 dispatch 字典中只挂 doc/none，sql/hybrid 分支 `route` 返回时临时降级走 doc/none，Task 7 再接入。）

- [ ] **Step 4: 跑测试通过 + 自测题文件准备**

Run: `python -X utf8 -m pytest tests/test_verify.py -v`
Expected: 2 passed

准备 `questions/selftest.jsonl`（8 题，question_id=q1..q8，题目原文）：
```jsonl
{"question_id": "q1", "question": "丽岛新材料本次IPO预计募集资金总额是多少？"}
{"question_id": "q2", "question": "列出丽岛新材料招股书中披露的全部风险因素。"}
{"question_id": "q3", "question": "苏州东微半导体股份有限公司本次募集资金投资项目拟投入募集资金合计多少？"}
{"question_id": "q4", "question": "苏州东微半导体本次公开发行股数是多少？占发行后总股本的比例是多少？"}
{"question_id": "q5", "question": "苏州东微半导体本次每股发行价格是多少？"}
{"question_id": "q6", "question": "列出苏州东微半导体招股意向书披露的全部风险因素（按类别）。"}
{"question_id": "q7", "question": "湖南国科微电子股份有限公司2016年营业收入是多少？较2015年增长多少？"}
{"question_id": "q8", "question": "湖南长远锂业股份有限公司本次发行股数是多少？"}
```

- [ ] **Step 5: E2E 冒烟——单题 Q4 真实跑通**

Run: `python -X utf8 -c "from run import *; c=get_conn(); init_db(c); r=answer_one(c,'q4','苏州东微半导体本次公开发行股数是多少？占发行后总股本的比例是多少？'); print(r.model_dump_json())"`
Expected: number/text 型答案，citations 非空且 quote 校验通过；若拒答检查检索阈值

- [ ] **Step 6: Commit**

```bash
git add run.py tests/test_verify.py questions/selftest.jsonl
git commit -m "feat: doc路P0闭环——生成+quote程序化逐字校验+三层拒答+CLI主循环"
```

---

### Task 6: 数值计算工具 + 数值题管线

**Files:**
- Modify: `run.py`（追加）
- Test: `tests/test_calc.py`

**Interfaces:**
- Produces: `run.unit_convert(v: float, frm: str, to: str) -> float`；`run.growth(a: float, b: float) -> float`（(b-a)/a）；`run.eval_intent(intent: dict) -> dict`（执行 `{op: convert|growth|ratio|sum, ...}`）；`run.answer_numeric(question_id, question, doc_id, extracted) -> AnswerRecord`（在 answer_doc 后处理数值）

- [ ] **Step 1: 写单测**

tests/test_calc.py：
```python
from run import unit_convert, growth, eval_intent

def test_unit_convert():
    assert unit_convert(1.5, "亿元", "万元") == 15000.0
    assert unit_convert(5000, "万元", "亿元") == 0.5
    assert unit_convert(12.5, "元", "元") == 12.5
    assert unit_convert(3.2, "%", "%") == 3.2

def test_growth():
    assert abs(growth(30000, 39000) - 0.3) < 1e-9

def test_eval_intent():
    assert eval_intent({"op": "convert", "value": 2, "from": "亿元", "to": "万元"})["number"] == 20000
    assert abs(eval_intent({"op": "growth", "base": 30000, "now": 39000})["number"] - 30.0) < 1e-9
    assert eval_intent({"op": "sum", "values": [1.2, 2.3], "unit": "亿元"})["number"] == 3.5
    assert abs(eval_intent({"op": "ratio", "part": 2500, "total": 10000})["number"] - 25.0) < 1e-9
```

- [ ] **Step 2: 验证失败 → Step 3 实现（追加 run.py）**

```python
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

_CALC_SYSTEM = """你负责把问题中的计算需求转成计算意图 JSON，禁止自己算出结果。
可用 op：convert{value,from,to} growth{base,now} ratio{part,total} sum{values,unit}。
单位只允许：元/万元/亿元/%/股。只输出 JSON 数组（每个计算一个对象），无计算则输出 []。"""

def numeric_postprocess(question: str, rec) -> None:
    """answer_doc 之后：若问题是数值计算类，用确定性工具重算 value。"""
    if rec.answer_type not in ("number",):
        return
    content, _u = llm.chat(_CALC_SYSTEM, question)
    m = re.search(r"\[.*\]", content, re.S)
    intents = json.loads(m.group(0)) if m else []
    results = [eval_intent(i) for i in intents]
    if results:
        rec.value = schema.Value(**results[0])
        if len(results) > 1:  # 多问（如"是多少？增长多少？"）拼接进 answer
            rec.answer = rec.answer  # 主值进 value，次值由 answer 文本承载（含原文明示数字）
```

（`numeric_postprocess` 在 `answer_one` 的 doc 分支后调用：`rec = answer_doc(...); numeric_postprocess(question, rec)`。）

- [ ] **Step 4: 跑测试通过 + E2E Q7**

Run: `python -X utf8 -m pytest tests/test_calc.py -v` → 3 passed
Run: `python -X utf8 -c "from run import *; c=get_conn(); init_db(c); print(answer_one(c,'q7','湖南国科微电子股份有限公司2016年营业收入是多少？较2015年增长多少？').model_dump_json())"`
Expected: value.number 为 2016 营收（万元/亿元换算正确）；growth 值在 answer 中；citations 页码正确

- [ ] **Step 5: Commit**

```bash
git add run.py tests/test_calc.py
git commit -m "feat: 数值确定性计算——单位换算/增长率/比例/合计意图执行，LLM零心算"
```

---

### Task 7: SQL 路 + 安全校验 + hybrid 最小版

**Files:**
- Modify: `run.py`（追加）
- Test: `tests/test_sqlguard.py`

**Interfaces:**
- Produces: `run.sql_guard(sql: str) -> tuple[bool, str]`（合法+强制 LIMIT 返回 (True, sql')）；`run.build_schema_cards(conn) -> str`（比赛库 10 表 schema 卡片）；`run.answer_sql(conn, qid, question, doc_id) -> AnswerRecord`；`run.answer_hybrid(...)`

- [ ] **Step 1: 写安全校验单测（含注入样例）**

tests/test_sqlguard.py：
```python
from run import sql_guard

def test_select_ok_and_limit_added():
    ok, sql = sql_guard("SELECT * FROM A基金日行情 WHERE 收盘价(元) > 10")
    assert ok and "LIMIT" in sql.upper()

def test_write_rejected():
    for bad in ["DELETE FROM 基金基本信息", "DROP TABLE x",
                "UPDATE 基金股票持仓明细 SET 数量=0",
                "SELECT 1; DROP TABLE x", "ATTACH DATABASE 'a' AS b",
                "PRAGMA journal_mode=off", "INSERT INTO t VALUES(1)"]:
        ok, _ = sql_guard(bad)
        assert not ok, bad

def test_multi_statement_rejected():
    ok, _ = sql_guard("SELECT 1; SELECT 2")
    assert not ok
```

- [ ] **Step 2: 验证失败 → Step 3 实现（追加 run.py）**

```python
# ---------- SQL 守卫 ----------
import sqlglot
from sqlglot import expressions as exp

def sql_guard(sql: str) -> tuple[bool, str]:
    """白名单校验：单语句、纯 SELECT、无写/DDL/附加，自动强制 LIMIT 200。"""
    try:
        stmts = sqlglot.parse(sql, read="sqlite")
    except Exception:
        return False, ""
    if len(stmts) != 1 or not isinstance(stmts[0], exp.Select):
        return False, ""
    bad = (exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create, exp.Alter,
           exp.Pragma, exp.Attach, exp.Copy, exp.Command)
    if stmts[0].find(*bad):
        return False, ""
    if not stmts[0].args.get("limit"):
        sql = f"SELECT * FROM ({sql}) LIMIT 200"
    return True, sql

# ---------- 比赛库 schema 卡片 ----------
COMPETITION_DB = str(Path(__file__).parent / "data" / "dataset" / "博金杯比赛数据.db")

def build_schema_cards() -> str:
    ro = sqlite3.connect(f"file:{COMPETITION_DB}?mode=ro", uri=True)
    cards = []
    for (tname,) in ro.execute("SELECT name FROM sqlite_master WHERE type='table'"):
        cols = [r[1] for r in ro.execute(f"PRAGMA table_info('{tname}')")]
        n = ro.execute(f"SELECT COUNT(*) FROM '{tname}'").fetchone()[0]
        cards.append(f"表 {tname}（{n} 行）：{', '.join(cols)}")
    ro.close()
    return "\n".join(cards)

_SQL_SYSTEM = """你是 Text-to-SQL 助手。只输出一条只读 SQLite SELECT 语句，不要解释。
字段名带单位（如 收盘价(元)），日期字段按字符串比较（如 '2020-12-31'）。"""

def answer_sql(conn, qid: str, question: str, doc_id: str | None) -> "AnswerRecord":
    content, usage = llm.chat(_SQL_SYSTEM,
                              f"Schema：\n{build_schema_cards()}\n\n问题：{question}")
    sql = content.strip().strip("`").removeprefix("sql").strip()
    ok, safe_sql = sql_guard(sql)
    if not ok:
        return refuse(qid, question, "生成的 SQL 未通过安全校验", "sql")
    ro = sqlite3.connect(f"file:{COMPETITION_DB}?mode=ro", uri=True)
    rows = ro.execute(safe_sql).fetchall(); cols = [d[0] for d in ro.execute(safe_sql).description]
    ro.close()
    ans = "; ".join("，".join(f"{c}={v}" for c, v in zip(cols, r)) for r in rows[:10])
    return schema.AnswerRecord(question_id=qid, answer=ans or "查询无结果",
                               answer_type="text", sql=safe_sql, route="sql",
                               confidence=0.7, tokens=usage)

def answer_hybrid(conn, qid: str, question: str, doc_id: str) -> "AnswerRecord":
    """最小版：doc 路为主，sql 路结果拼进 answer，route=hybrid。"""
    rec = answer_doc(conn, qid, question, doc_id)
    try:
        srec = answer_sql(conn, qid, question, doc_id)
        if srec.sql:
            rec.sql, rec.route = srec.sql, "hybrid"
            rec.answer += f"｜数据库侧：{srec.answer}"
    except Exception:  # noqa: BLE001 sql 侧失败不拖垮 doc 侧
        pass
    return rec
```

（`answer_one` 的 dispatch 恢复挂载 sql/hybrid 分支。）

- [ ] **Step 4: 跑测试通过 + E2E 手测一道基金题**

Run: `python -X utf8 -m pytest tests/test_sqlguard.py -v` → 3 passed
Run: `python -X utf8 -c "from run import *; c=get_conn(); init_db(c); print(answer_one(c,'t1','2020年基金持仓中股票数量最多的基金是哪只？').model_dump_json())"`
Expected: route=sql，sql 字段含 SELECT+LIMIT，答案来自比赛库

- [ ] **Step 5: Commit**

```bash
git add run.py tests/test_sqlguard.py
git commit -m "feat: sql路——sqlglot白名单守卫+强制LIMIT+只读连接+schema卡片；hybrid最小版"
```

---

### Task 8: 长列表完整召回 + 多口径最小版

**Files:**
- Modify: `run.py`（追加）
- Test: `tests/test_section.py`

**Interfaces:**
- Produces: `run.locate_section_chunks(conn, doc_id, section_kw: str) -> list[dict]`（标题树定位章节，整章全量）；`run.answer_listq(conn, qid, question, doc_id) -> AnswerRecord`（items+条目数，程序校验）

- [ ] **Step 1: 写单测**

tests/test_section.py：
```python
import sqlite3
from ingest import init_db
from run import locate_section_chunks

def test_locate_whole_section():
    c = sqlite3.connect(":memory:"); init_db(c)
    rows = [(1, "第一节 释义\n发行人指苏州东微"), (2, "第二节 概览\n公司主营功率半导体"),
            (3, "第四节 风险因素\n（一）技术风险\n产品迭代风险"), (4, "（二）市场风险\n价格波动风险")]
    for pg, txt in rows:
        c.execute("INSERT INTO pages VALUES ('d1', ?, NULL, ?)", (pg, txt))
        for line in txt.split("\n") if False else [txt]:  # 简化：整页一个chunk
            cur = c.execute("INSERT INTO chunks(doc_id,pdf_page,text) VALUES ('d1',?,?)", (pg, line))
            c.execute("INSERT INTO chunks_fts(rowid,text) VALUES (?,?)", (cur.lastrowid, line))
    sec = locate_section_chunks(c, "d1", "风险因素")
    assert {s["pdf_page"] for s in sec} == {3, 4}  # 整章全量，非 top-k
```

- [ ] **Step 2: 验证失败 → Step 3 实现（追加 run.py）**

```python
# ---------- 长列表：章节定位 + 整章召回 ----------
_SEC_START = re.compile(r"第[一二三四五六七八九十百]+节\s*(.+)")

def locate_section_chunks(conn, doc_id: str, section_kw: str) -> list[dict]:
    """标题树找「风险因素」类章节起点，收录到下一节标题前的全部 chunks。"""
    allc = conn.execute(
        "SELECT chunk_id, pdf_page, text FROM chunks WHERE doc_id=? ORDER BY pdf_page, chunk_id",
        (doc_id,)).fetchall()
    inside, started = [], False
    for cid, pg, text in allc:
        m = _SEC_START.search(text[:60])
        if m:
            if started:
                break  # 下一节开始 → 收束
            started = section_kw in m.group(1)
        elif started:
            inside.append({"chunk_id": cid, "doc_id": doc_id, "pdf_page": pg, "text": text})
    return inside

_LIST_HINT = re.compile(r"列出|全部|哪些|分别")

def answer_listq(conn, qid: str, question: str, doc_id: str) -> "AnswerRecord":
    kw = "风险因素" if "风险" in question else "募集"
    secs = locate_section_chunks(conn, doc_id, kw)
    ctx = "\n\n".join(f"[pdf_page={s['pdf_page']}]\n{s['text']}" for s in secs[:60])  # 整章上限60块
    sysp = """你是招股书结构化助手。按原文层级列出全部条目，禁止增删改写。
输出 JSON：{"items": [str], "citations": [{"pdf_page": int, "quote": str}]}，items 每项一条，quote 为该项在原文的连续片段。"""
    content, usage = llm.chat(sysp, f"问题：{question}\n\n章节内容：\n{ctx}")
    m = re.search(r"\{.*\}", content, re.S)
    data = json.loads(m.group(0)) if m else {}
    items, cites = data.get("items") or [], []
    for ct in data.get("citations", []):
        cand = {"doc_id": doc_id, "pdf_page": ct.get("pdf_page", 0), "quote": ct.get("quote", "")}
        if verify_quote(conn, cand):
            pr = conn.execute("SELECT printed_page FROM pages WHERE doc_id=? AND pdf_page=?",
                              (doc_id, cand["pdf_page"])).fetchone()
            cites.append({**cand, "printed_page": pr[0] if pr else None})
    n = len(items)
    return schema.AnswerRecord(
        question_id=qid, answer=f"共 {n} 项", answer_type="list",
        items=items, citations=[schema.Citation(**c) for c in cites],
        route="doc", confidence=0.8 if cites else 0.3, tokens=usage)
```

多口径最小版：`answer_doc` 的 `_DOC_SYSTEM` 追加一条规则行——「若问题涉及的指标存在合并报表/母公司报表等不同口径，或不同报告类型/行业分类标准，须在 answer 中分别给出各口径数值并注明差异，每种口径各给一条 citation」。E2E Q7 验证（2016 营收：合并利润表口径）。

`answer_one` 的 doc 分支前加列表题判定：`if _LIST_HINT.search(question) and "风险" in question: rec = answer_listq(...)`。

- [ ] **Step 4: 跑测试通过 + E2E Q6**

Run: `python -X utf8 -m pytest tests/test_section.py -v` → 1 passed
Run: `python -X utf8 -c "from run import *; c=get_conn(); init_db(c); print(len(answer_one(c,'q6','列出苏州东微半导体招股意向书披露的全部风险因素（按类别）。').items))"`
Expected: items 数十条（风险因素章通常 30–60 项），answer 含"共 N 项"

- [ ] **Step 5: Commit**

```bash
git add run.py tests/test_section.py
git commit -m "feat: 长列表章节全量召回+条目数程序校验+多口径prompt规则"
```

---

### Task 9: 8 题全量跑 + 差距修复 + results/ 产出

**Files:**
- Create: `results/answers.jsonl`（产物）
- Modify: `run.py`（按差距修）

- [ ] **Step 1: 全量跑 8 题**

Run: `python -X utf8 run.py --input questions/selftest.jsonl --output results/answers.jsonl`
Expected: 8 行 JSON 全部符合 Schema；q1/q2/q8=refusal（库外公司）、q5=refusal（未披露）、q3/q4=number、q6=list、q7=number+计算

- [ ] **Step 2: 逐题核对差距（对照 PDF 原文人工看）**

检查清单：q3 表格合计数与 PDF 募投表一致；q4 股数+比例两问都有；q5 拒答理由提到招股意向书未定价；q7 营收口径+增速换算。每处差距回改对应环节（检索阈值/表格解析/prompt 规则），重跑。

- [ ] **Step 3: Commit**

```bash
git add results/answers.jsonl run.py
git commit -m "feat: 8题全量产出+差距修复，results/交付物"
```

---

### Task 10: 标注 + evaluate.py 指标

**Files:**
- Create: `evaluate.py`
- Create: `labels.jsonl`
- Test: `tests/test_evaluate.py`

**Interfaces:**
- Consumes: `schema.AnswerRecord`
- Produces: CLI `python -X utf8 evaluate.py --answers results/answers.jsonl --labels labels.jsonl [--dump-template questions/selftest.jsonl]`；输出五组指标到 stdout + `results/metrics.json`

- [ ] **Step 1: 写指标单测**

tests/test_evaluate.py：
```python
from evaluate import numeric_correct, list_prf, citation_acc, refusal_pr

def test_numeric():
    assert numeric_correct({"answer_type": "number", "value": {"number": 49.75, "unit": "亿元"}},
                           {"answer_type": "number", "value": {"number": 50.0, "unit": "亿元"}})
    assert not numeric_correct({"answer_type": "number", "value": {"number": 40.0, "unit": "亿元"}},
                               {"answer_type": "number", "value": {"number": 50.0, "unit": "亿元"}})

def test_list_prf():
    pred = {"answer_type": "list", "items": ["技术风险", "市场风险", "政策风险"]}
    gold = {"answer_type": "list", "items": ["技术风险", "市场风险", "经营风险", "政策风险"]}
    p, r, f1 = list_prf(pred, gold)
    assert p == 0.75 or abs(p - 0.75) < 1e-9
    assert abs(r - 3 / 4) < 1e-9

def test_citation_and_refusal():
    a = {"answer_type": "number", "citations": [{"doc_id": "d", "pdf_page": 3, "quote": "x", "verified": True}]}
    assert citation_acc(a, {"citations_expected": 1}) == 1.0
    p, r = refusal_pr(
        [{"q": "q1", "answer_type": "refusal"}, {"q": "q4", "answer_type": "number"}],
        [{"q": "q1", "expect_refusal": True}, {"q": "q4", "expect_refusal": False}])
    assert p == 1.0 and r == 1.0
```

- [ ] **Step 2: 验证失败 → Step 3 实现 evaluate.py**

```python
"""自测评估：python -X utf8 evaluate.py --answers A --labels L [--dump-template Q]"""
import argparse
import json
import statistics

def numeric_correct(pred: dict, gold: dict, tol: float = 0.005) -> bool:
    if pred["answer_type"] != "number":
        return False
    pv, gv = pred.get("value") or {}, gold.get("value") or {}
    if pv.get("number") is None or gv.get("number") is None:
        return False
    pu, gu = pv.get("unit"), gv.get("unit")
    v = pv["number"]
    if pu != gu and pu in ("元", "万元", "亿元") and gu in ("元", "万元", "亿元"):
        fac = {"元": 1, "万元": 1e4, "亿元": 1e8}
        v = v * fac[pu] / fac[gu]
    return abs(v - gv["number"]) / max(abs(gv["number"]), 1e-9) <= tol

def list_prf(pred: dict, gold: dict) -> tuple[float, float, float]:
    ps = [i.strip() for i in pred.get("items") or []]
    gs = [i.strip() for i in gold.get("items") or []]
    gs_set, ps_set = set(gs), set(ps)
    tp = len([p for p in ps if p in gs_set])
    p = tp / len(ps) if ps else 0.0
    r = tp / len(gs) if gs else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f1

def citation_acc(pred: dict, gold: dict) -> float:
    cites = pred.get("citations") or []
    if not cites:
        return 0.0
    ok = sum(1 for c in cites if c.get("verified"))
    return ok / len(cites)

def refusal_pr(preds: list[dict], golds: list[dict]) -> tuple[float, float]:
    g = {x["q"]: x["expect_refusal"] for x in golds}
    tp = fp = fn = 0
    for p in preds:
        pr = p["answer_type"] == "refusal"
        if pr and g.get(p["q"]):
            tp += 1
        elif pr and not g.get(p["q"]):
            fp += 1
        elif not pr and g.get(p["q"]):
            fn += 1
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    return prec, rec

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--answers", required=True)
    ap.add_argument("--labels", required=True)
    ap.add_argument("--dump-template")
    args = ap.parse_args()
    if args.dump_template:
        with open(args.dump_template, encoding="utf-8") as f:
            for line in f:
                item = json.loads(line)
                print(json.dumps({"q": item["question_id"], "question": item["question"],
                                  "answer_type": None, "value": None, "items": None,
                                  "expect_refusal": None,
                                  "citations_expected": None}, ensure_ascii=False))
        return
    answers = [json.loads(l) for l in open(args.answers, encoding="utf-8") if l.strip()]
    labels = {x["q"]: x for x in (json.loads(l) for l in open(args.labels, encoding="utf-8") if l.strip())}
    nums = [(a, labels[a["question_id"]]) for a in answers
            if labels.get(a["question_id"], {}).get("answer_type") == "number"]
    lists_ = [(a, labels[a["question_id"]]) for a in answers
              if labels.get(a["question_id"], {}).get("answer_type") == "list"]
    lat = sorted(a["latency_ms"] for a in answers)
    cost = [a["tokens"]["input"] + a["tokens"]["output"] for a in answers]
    metrics = {
        "数值题准确率(±0.5%)": (sum(numeric_correct(a, g) for a, g in nums) / len(nums)) if nums else None,
        "列表P/R/F1": ([list_prf(a, g) for a, g in lists_] or None),
        "引用正确率": (sum(citation_acc(a, g) for a, g in nums + lists_) / len(nums + lists_)) if nums + lists_ else None,
        "拒答P/R": refusal_pr([{"q": a["question_id"], "answer_type": a["answer_type"]} for a in answers],
                              [{"q": q, "expect_refusal": l["expect_refusal"]}
                               for q, l in labels.items() if l["expect_refusal"] is not None]),
        "延迟avg/P95_ms": [int(statistics.mean(lat)), lat[int(0.95 * (len(lat) - 1))]],
        "单题平均tokens": int(statistics.mean(cost)) if cost else 0,
    }
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    json.dump(metrics, open("results/metrics.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
```

注：`citation_acc` 依赖 answers.jsonl 里 citation 带 `verified` 标记——Task 5 的 `verify_quote` 已在产出时过滤假引用，此处 `verified=True` 由 run.py 输出时写入（在 AnswerRecord 外层附加字段或 citations dict 加 key；实现时在 `main()` 写行前给每条 citation 附 `"verified": verify_quote(conn, c)`）。

- [ ] **Step 4: 跑单测通过 → 标注 8 题（人工核对 PDF 原页）**

Run: `python -X utf8 -m pytest tests/test_evaluate.py -v` → 4 passed
标注：`python -X utf8 evaluate.py --dump-template questions/selftest.jsonl > labels.jsonl`，逐题打开原 PDF（doc_id 用公司名在 knowledge.db docs 表反查）核对页码与数值，填 answer_type/value/items/expect_refusal/citations_expected。

- [ ] **Step 5: 跑正式评估出指标**

Run: `python -X utf8 evaluate.py --answers results/answers.jsonl --labels labels.jsonl`
Expected: 五组指标输出，results/metrics.json 生成

- [ ] **Step 6: Commit**

```bash
git add evaluate.py labels.jsonl tests/test_evaluate.py results/metrics.json
git commit -m "feat: 评估程序五组指标+8题人工标注(核对PDF原页)"
```

---

### Task 11: README + design.md + 交付收尾

**Files:**
- Create: `README.md`
- Create: `design.md`

- [ ] **Step 1: 写 README.md**

必须包含（成稿时按实际模型名/命令填写）：
- 项目简介（题目二任务一句话）
- 环境要求：Python 3.12、`pip install -r requirements.txt`
- **数据集下载**（醒目章节）：`pip install modelscope && modelscope download --dataset BJQW14Bbs_challenge_financial_14b_dataset --local_dir data/`，目录结构说明（pdf/pdf_txt_file/dataset/question.json）
- API key 环境变量：`DEEPSEEK_API_KEY`、`ZHIPU_API_KEY`
- 复现步骤：① `python -X utf8 ingest.py`（建库）② `python -X utf8 run.py --input questions/selftest.jsonl --output results/answers.jsonl` ③ `python -X utf8 evaluate.py --answers results/answers.jsonl --labels labels.jsonl`
- 所用模型：deepseek-chat（生成）、embedding-3（向量化）
- 输出 Schema 说明 + results/ 目录说明
- 已知限制（表格解析边界、SQL 路覆盖的表）

- [ ] **Step 2: 写 design.md（从 spec.md 提炼，面向出题方，≤1 页）**

结构：架构图（spec §3）→ 存储设计（spec §4 表格）→ 管线设计要点（spec §5/6 各条压缩）→ 评估结果（metrics.json 数字）→ 设计取舍（为什么 quote 程序化校验/为什么 LLM 零心算/实体链接桥梁方案）。

- [ ] **Step 3: 全套验收检查**

Run: `python -X utf8 -m pytest -v`（全部绿）
Run: `python -X utf8 run.py --input questions/selftest.jsonl --output results/answers.jsonl && python -X utf8 evaluate.py --answers results/answers.jsonl --labels labels.jsonl`
Expected: 全链路一次跑通，results/ 含 answers.jsonl + metrics.json

- [ ] **Step 4: Commit + push（交付）**

```bash
git add README.md design.md results/
git commit -m "docs: README(含数据集下载/复现步骤)+design.md——交付收尾"
git push
```

---

## Self-Review 结论

- **Spec 覆盖**：P0 五项 → Task 1–5（入库/问答/溯源/拒答/Schema）；P1.1 路由+SQL+实体链接 → Task 4/7；P1.2 数值计算 → Task 6；P1.3 长列表 → Task 8；P1.4 多口径 → Task 8 prompt 规则+Q7 验证；P1.5 评估 → Task 9/10；交付物 → Task 11。question.json 1000 题抽样 = 砍单项（§9），未列任务，符合 spec。
- **占位符**：Task 5 Step 3 注明 sql/hybrid 接线时序（先降级后接入），Task 7 补齐——无 TBD。
- **类型一致性**：AnswerRecord/Value/Citation 全程一致；verify_quote 消费 dict、Citation 产出 dict 字段名一致（printed_page）。
