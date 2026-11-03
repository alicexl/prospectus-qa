from run import sql_guard


def test_select_ok_and_limit_added():
    ok, sql = sql_guard("SELECT * FROM 基金日行情 WHERE 收盘价 > 10")
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
