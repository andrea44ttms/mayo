import functools
import logging
from typing import Callable, Any

from .rate_limiter import api_limiter, comment_limiter

logger = logging.getLogger(__name__)


def rate_limited(limiter_type: str = "api", timeout: float = 15.0):
    """
    Decorator to apply rate limiting to a function.
    The first argument of the decorated function must be installation_id.

    Usage:
        @rate_limited("comment")
        def post_comment(installation_id, repo, body): ...
    """
    limiter = api_limiter if limiter_type == "api" else comment_limiter

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Derive key from first positional arg or kwarg
            key = str(args[0]) if args else str(kwargs.get("installation_id", "default"))
            acquired = limiter.wait_and_acquire(key, timeout=timeout)
            if not acquired:
                logger.warning(
                    "Rate limit exceeded for %s on key=%s (limiter=%s)",
                    func.__name__,
                    key,
                    limiter_type,
                )
                raise RuntimeError(
                    f"Rate limit exceeded for installation {key}. "
                    f"Try again in a moment."
                )
            logger.debug(
                "Rate limit OK: %s remaining slots for key=%s",
                limiter.remaining(key),
                key,
            )
            return func(*args, **kwargs)

        return wrapper

    return decorator
