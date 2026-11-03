import sqlite3

from ingest import init_db
from run import locate_section_chunks


def test_locate_whole_section():
    c = sqlite3.connect(":memory:")
    init_db(c)
    rows = [(1, "第一节 释义\n发行人：指苏州东微"), (2, "第二节 概览\n公司主营功率半导体"),
            (3, "第四节 风险因素\n（一）技术风险\n产品迭代风险"), (4, "（二）市场风险\n价格波动风险"),
            (5, "第五节 募集资金运用\n募投项目说明")]
    for pg, txt in rows:
        cur = c.execute("INSERT INTO chunks(doc_id,pdf_page,text) VALUES ('d1',?,?)", (pg, txt))
        c.execute("INSERT INTO chunks_fts(rowid,text) VALUES (?,?)", (cur.lastrowid, txt))
    sec = locate_section_chunks(c, "d1", "风险因素")
    assert {s["pdf_page"] for s in sec} == {3, 4}  # 整章全量：到下一节标题前
