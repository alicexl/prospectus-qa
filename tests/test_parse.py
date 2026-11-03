from ingest import parse_printed_page


def test_printed_page_patterns():
    assert parse_printed_page("第 1-1-3 页") == "1-1-3"
    assert parse_printed_page("第一节 释义 第1-1-15页") == "1-1-15"
    assert parse_printed_page("第 12 页 共 300 页") == "12"
    assert parse_printed_page("1-2-8") == "1-2-8"
    assert parse_printed_page("17") == "17"
    assert parse_printed_page("风险因素提示") is None
    assert parse_printed_page("公司拟公开发行股票") is None
