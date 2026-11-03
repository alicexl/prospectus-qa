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
    assert d["value"]["number"] is None and d["items"] == [] and d["sql"] is None \
        and d["tokens"] == {"input": 0, "output": 0}
