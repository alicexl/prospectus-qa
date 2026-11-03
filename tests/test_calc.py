from run import unit_convert, growth, eval_intent


def test_unit_convert():
    assert unit_convert(1.5, "亿元", "万元") == 15000.0
    assert unit_convert(5000, "万元", "亿元") == 0.5
    assert unit_convert(12.5, "元", "元") == 12.5
    assert unit_convert(3.2, "%", "%") == 3.2


def test_growth():
    assert abs(growth(30000, 39000) - 0.3) < 1e-9


def test_eval_intent():
    assert eval_intent({"op": "convert", "value": 2, "from": "亿元", "to": "万元"})["number"] == 20000
    assert abs(eval_intent({"op": "growth", "base": 30000, "now": 39000})["number"] - 30.0) < 1e-9
    assert eval_intent({"op": "sum", "values": [1.2, 2.3], "unit": "亿元"})["number"] == 3.5
    assert abs(eval_intent({"op": "ratio", "part": 2500, "total": 10000})["number"] - 25.0) < 1e-9
