"""P0#1 专项2：表格结构化保留 + 跨页表格合并——基于真实数据的验证。
数据集/知识库未就绪时自动跳过。"""
import glob
import json as jsonlib
import sqlite3
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
PDF_DIR = ROOT / "data" / "pdf"
DB = ROOT / "data" / "knowledge.db"


def _db_docs() -> int:
    if not DB.exists():
        return 0
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        return c.execute("SELECT COUNT(*) FROM docs").fetchone()[0]
    finally:
        c.close()


@pytest.mark.skipif(_db_docs() == 0, reason="knowledge.db 未建/为空")
def test_blocks_tables_structured():
    """blocks.table_json 必须是结构化二维表（行列保留），非扁平文本。"""
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        rows = c.execute(
            "SELECT table_json FROM blocks WHERE type='table' ORDER BY RANDOM() LIMIT 200"
        ).fetchall()
    finally:
        c.close()
    assert len(rows) >= 50, "抽样不足：表格入库量异常"
    valid = 0
    for (tj,) in rows:
        t = jsonlib.loads(tj)
        assert isinstance(t, list) and all(isinstance(r, list) for r in t)
        if len(t) >= 2 and max(len(r) for r in t) >= 2:
            valid += 1
    assert valid / len(rows) >= 0.8, f"有效二维表占比过低：{valid}/{len(rows)}"


def _smallest_pdfs(n: int) -> list[str]:
    pdfs = sorted(set(glob.glob(str(PDF_DIR / "*.PDF"))) | set(glob.glob(str(PDF_DIR / "*.pdf"))))
    return sorted(pdfs, key=lambda p: Path(p).stat().st_size)[:n]


@pytest.mark.skipif(not PDF_DIR.is_dir() or not any(PDF_DIR.glob("*.PDF")),
                    reason="数据集未下载")
def test_cross_page_merge_on_real_pdf():
    """真实 PDF 上验证跨页合并：相邻页表头相似的表必须合并为单条目（表头去重）。"""
    from ingest import _header_similar, merge_cross_page_tables, parse_pdf

    merged_any = False
    checked_pairs = 0
    for pdf in _smallest_pdfs(2):
        parsed = parse_pdf(pdf)
        raw = []
        for p in parsed["pages"]:
            for t in p["tables"]:
                if t:
                    raw.append((p["pdf_page"], t))
        for (pg1, t1), (pg2, t2) in zip(raw, raw[1:]):
            if pg2 - pg1 <= 1 and _header_similar(t1, t2):
                checked_pairs += 1
                merged = merge_cross_page_tables(
                    [{"pdf_page": pg1, "tables": [t1]}, {"pdf_page": pg2, "tables": [t2]}])
                assert len(merged) == 1, f"{Path(pdf).name} p{pg1}->p{pg2} 未合并"
                rows = merged[0]["rows"]
                hdr = ["" if c is None else c for c in t1[0]]  # _clean_rows 把 None 转空串
                assert rows.count(hdr) == 1, "续页表头未去重"
                for r in t2[1:]:  # 续页数据行必须并入
                    if any(str(c or "").strip() for c in r):
                        assert [("" if c is None else c) for c in r] in rows
                merged_any = True
    if checked_pairs == 0:
        pytest.skip("样本文档未出现跨页同表头表格对")
    assert merged_any, f"检查了 {checked_pairs} 对跨页表均未合并"
