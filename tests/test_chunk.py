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
    assert ["研发中心", "20,000"] in m0["rows"]   # 续页数据并入
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
