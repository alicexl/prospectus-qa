"""P0#1 专项：文档ID + PDF物理页码 + 印刷页码（含 1-1-xx 格式）三层溯源链落库检查。
真实 PDF 集成测试——数据集未下载时自动跳过。"""
import re
import sqlite3
import tempfile
from pathlib import Path

import pytest

PDF_DIR = Path(__file__).parent.parent / "data" / "pdf"

_have_pdfs = PDF_DIR.is_dir() and any(PDF_DIR.glob("*.PDF")) or any(PDF_DIR.glob("*.pdf"))


@pytest.mark.skipif(not _have_pdfs, reason="数据集未下载（data/pdf 为空）")
def test_docid_pdfpage_printedpage_chain():
    import glob

    from ingest import _write_doc, get_conn, init_db, parse_pdf

    pdf = sorted(set(glob.glob(str(PDF_DIR / "*.PDF"))) | set(glob.glob(str(PDF_DIR / "*.pdf"))))[0]
    with tempfile.TemporaryDirectory() as td:
        conn = get_conn(str(Path(td) / "t.db"))
        init_db(conn)
        parsed = parse_pdf(pdf)
        _write_doc(conn, parsed)

        doc_id = Path(pdf).stem
        # ① 文档ID = PDF 文件名（哈希）
        assert conn.execute("SELECT doc_id FROM docs").fetchall() == [(doc_id,)]
        # ② PDF 物理页码：1..N 连续不缺
        pgs = [r[0] for r in conn.execute(
            "SELECT pdf_page FROM pages WHERE doc_id=? ORDER BY pdf_page", (doc_id,))]
        assert pgs == list(range(1, len(parsed["pages"]) + 1))
        # ③ 印刷页码：识别率 ≥90%（首尾扉页可无页码），且保持字符串原样
        rows = conn.execute(
            "SELECT pdf_page, printed_page FROM pages WHERE doc_id=? ORDER BY pdf_page",
            (doc_id,)).fetchall()
        n_printed = sum(1 for _, p in rows if p is not None)
        assert n_printed / len(rows) >= 0.9
        for _, p in rows:
            if p is not None:
                assert isinstance(p, str) and re.fullmatch(r"[\d\-]+", p)
        # ④ 印刷页码随物理页单调递增（数值语义正确，非乱抓）
        nums = [int(p.replace("-", "")) if p else None for _, p in rows]
        seq = [x for x in nums if x is not None]
        assert seq == sorted(seq)
        conn.close()  # Windows: 必须先关连接释放 WAL，TemporaryDirectory 才能清理
