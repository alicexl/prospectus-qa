import sqlite3

from ingest import init_db, upsert_doc, doc_exists


def test_init_and_idempotent():
    conn = sqlite3.connect(":memory:")
    init_db(conn)
    upsert_doc(conn, doc_id="abc", company_name="苏州东微半导体股份有限公司",
               stock_code="688261", doc_type="IPO", page_count=10)
    assert doc_exists(conn, "abc") is True
    assert doc_exists(conn, "nope") is False
    # FTS5 trigram 中文可用性
    conn.execute("INSERT INTO chunks_fts(rowid, text) VALUES (1, '募集资金总额为50,000万元')")
    hit = conn.execute("SELECT text FROM chunks_fts WHERE chunks_fts MATCH '募集资金'").fetchall()
    assert len(hit) == 1
