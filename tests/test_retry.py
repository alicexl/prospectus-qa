"""限流退避策略单测：普通异常快恢复、429 长退避 + retry-after 优先、60s 上限。"""
import llm


def test_backoff_normal_fast_recovery():
    assert [llm._retry_wait(i, False, None) for i in range(5)] == [1, 2, 4, 8, 16]


def test_backoff_rate_limited_caps_at_60():
    assert llm._retry_wait(0, True, None) == 10
    assert llm._retry_wait(3, True, None) == 60
    assert llm._retry_wait(4, True, None) == 60


def test_backoff_rate_limited_prefers_retry_after():
    assert llm._retry_wait(1, True, 30) == 30
    assert llm._retry_wait(4, True, 90) == 60  # 仍受 60s 上限约束
