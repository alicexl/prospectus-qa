import sqlite3

from ingest import init_db
from run import link_company, route, rrf


def _conn():
    c = sqlite3.connect(":memory:")
    init_db(c)
    return c


def test_link_company_longest_match():
    c = _conn()
    c.execute("INSERT INTO company_registry VALUES ('苏州东微半导体股份有限公司','d1','688261')")
    c.execute("INSERT INTO company_registry VALUES ('苏州东微半导体','d1','688261')")
    c.execute("INSERT INTO company_registry VALUES ('湖南国科微电子股份有限公司','d2','300672')")
    assert link_company(c, "苏州东微半导体股份有限公司本次公开发行股数是多少？") == "d1"
    assert link_company(c, "湖南国科微电子 2016 年营业收入是多少？") == "d2"
    assert link_company(c, "丽岛新材料本次IPO预计募集资金总额是多少？") is None


def test_route_rules():
    assert route("列出招股书中披露的全部风险因素", "d1") == "doc"
    assert route("东微半导体本次募集资金投资项目合计多少？", "d1") == "doc"
    assert route("丽岛新材料本次IPO预计募集资金总额是多少？", None) == "none"
    assert route("某基金2020年持仓了哪些股票？", None) == "sql"
    assert route("国科微2016年营收多少？基金持仓多少？", "d2") == "hybrid"


def test_rrf():
    assert rrf([["a"], ["b"]], [["b"], ["a"]])["a"] == rrf([["a"], ["b"]], [["b"], ["a"]])["b"]
    top = max(rrf([["x"], ["y"]], [["x"], ["z"]]).items(), key=lambda kv: kv[1])[0]
    assert top == "x"
