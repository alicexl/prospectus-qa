from evaluate import numeric_correct, list_prf, refusal_pr


def test_numeric():
    assert numeric_correct({"answer_type": "number", "value": {"number": 49.75, "unit": "亿元"}},
                           {"answer_type": "number", "value": {"number": 50.0, "unit": "亿元"}})
    assert not numeric_correct({"answer_type": "number", "value": {"number": 40.0, "unit": "亿元"}},
                               {"answer_type": "number", "value": {"number": 50.0, "unit": "亿元"}})
    # 单位不同但换算后等价
    assert numeric_correct({"answer_type": "number", "value": {"number": 50000, "unit": "万元"}},
                           {"answer_type": "number", "value": {"number": 5.0, "unit": "亿元"}})


def test_list_prf():
    pred = {"items": ["技术风险-产品迭代", "市场风险-价格波动", "政策风险-补贴退坡"]}
    gold = {"items": ["技术风险-产品迭代", "市场风险-价格波动", "经营风险-客户集中", "政策风险-补贴退坡"]}
    p, r, f1 = list_prf(pred, gold)
    assert abs(p - 1.0) < 1e-9
    assert abs(r - 0.75) < 1e-9
    assert abs(f1 - (2 * 1.0 * 0.75 / 1.75)) < 1e-9


def test_refusal_pr():
    p, r = refusal_pr(
        [{"q": "q1", "refused": True}, {"q": "q4", "refused": False}],
        {"q1": True, "q4": False})
    assert p == 1.0 and r == 1.0
    p2, r2 = refusal_pr(
        [{"q": "q1", "refused": False}, {"q": "q4", "refused": False}],
        {"q1": True, "q4": False})
    assert p2 == 0.0 and r2 == 0.0
