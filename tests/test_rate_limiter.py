import time
import threading
import pytest
from utils.rate_limiter import RateLimiter


def test_allows_requests_within_limit():
    limiter = RateLimiter(max_requests=3, window_seconds=60)
    assert limiter.is_allowed("inst_1") is True
    assert limiter.is_allowed("inst_1") is True
    assert limiter.is_allowed("inst_1") is True


def test_blocks_requests_over_limit():
    limiter = RateLimiter(max_requests=2, window_seconds=60)
    limiter.is_allowed("inst_2")
    limiter.is_allowed("inst_2")
    assert limiter.is_allowed("inst_2") is False


def test_keys_are_isolated():
    limiter = RateLimiter(max_requests=1, window_seconds=60)
    assert limiter.is_allowed("a") is True
    assert limiter.is_allowed("b") is True  # different key, fresh bucket
    assert limiter.is_allowed("a") is False


def test_window_expiry():
    limiter = RateLimiter(max_requests=1, window_seconds=1)
    assert limiter.is_allowed("inst_3") is True
    assert limiter.is_allowed("inst_3") is False
    time.sleep(1.1)
    assert limiter.is_allowed("inst_3") is True


def test_remaining_count():
    limiter = RateLimiter(max_requests=5, window_seconds=60)
    assert limiter.remaining("inst_4") == 5
    limiter.is_allowed("inst_4")
    limiter.is_allowed("inst_4")
    assert limiter.remaining("inst_4") == 3


def test_wait_and_acquire_succeeds():
    limiter = RateLimiter(max_requests=1, window_seconds=1)
    assert limiter.is_allowed("inst_5") is True
    # Should succeed after window expires
    result = limiter.wait_and_acquire("inst_5", timeout=2.0)
    assert result is True


def test_wait_and_acquire_timeout():
    limiter = RateLimiter(max_requests=1, window_seconds=60)
    limiter.is_allowed("inst_6")
    # Using a slightly longer timeout (0.8s) to reduce flakiness on slow CI
    result = limiter.wait_and_acquire("inst_6", timeout=0.8)
    assert result is False


def test_thread_safety():
    limiter = RateLimiter(max_requests=50, window_seconds=60)
    results = []

    def make_requests():
        for _ in range(10):
            results.append(limiter.is_allowed("shared"))

    threads = [threading.Thread(target=make_requests) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    allowed = sum(1 for r in results if r)
    assert allowed == 50
