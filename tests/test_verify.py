import sqlite3

from ingest import init_db
from run import norm_text, verify_quote


def test_norm_text():
    assert norm_text("募集 资金\n总额") == norm_text("募集资金总额")
    assert norm_text("５０００万元") == norm_text("5000万元")  # 全角数字
    assert norm_text("（元）") == norm_text("(元)")           # 全角括号


def test_verify_quote_on_page():
    c = sqlite3.connect(":memory:")
    init_db(c)
    c.execute("INSERT INTO pages VALUES ('d1', 3, '1-1-3', '本次发行募集资金总额为 50,000 万元。')")
    ok = verify_quote(c, {"doc_id": "d1", "pdf_page": 3, "quote": "募集资金总额为 50,000 万元"})
    bad_page = verify_quote(c, {"doc_id": "d1", "pdf_page": 4, "quote": "募集资金总额"})
    bad_text = verify_quote(c, {"doc_id": "d1", "pdf_page": 3, "quote": "不存在的文字"})
    assert ok and not bad_page and not bad_text
