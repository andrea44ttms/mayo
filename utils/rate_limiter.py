import time
import threading
from collections import defaultdict, deque


class RateLimiter:
    """
    Token-bucket style rate limiter for GitHub API calls.
    Tracks requests per installation to avoid hitting secondary rate limits.
    """

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._locks: dict[str, threading.Lock] = defaultdict(threading.Lock)
        self._queues: dict[str, deque] = defaultdict(deque)

    def is_allowed(self, key: str) -> bool:
        """Check if a request is allowed for the given key."""
        now = time.monotonic()
        with self._locks[key]:
            q = self._queues[key]
            # Remove timestamps outside the window
            while q and now - q[0] > self.window_seconds:
                q.popleft()
            if len(q) < self.max_requests:
                q.append(now)
                return True
            return False

    def wait_and_acquire(self, key: str, timeout: float = 30.0) -> bool:
        """Block until a slot is available or timeout is reached."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.is_allowed(key):
                return True
            time.sleep(0.5)
        return False

    def remaining(self, key: str) -> int:
        """Return how many requests are still allowed in the current window."""
        now = time.monotonic()
        with self._locks[key]:
            q = self._queues[key]
            while q and now - q[0] > self.window_seconds:
                q.popleft()
            return max(0, self.max_requests - len(q))

    def reset(self, key: str) -> None:
        """Clear the request history for a given key (useful for testing)."""
        with self._locks[key]:
            self._queues[key].clear()


# Singleton instances
# Bumped api_limiter to 15 req/min to give a bit more headroom for my use case
api_limiter = RateLimiter(max_requests=15, window_seconds=60)
comment_limiter = RateLimiter(max_requests=5, window_seconds=60)
