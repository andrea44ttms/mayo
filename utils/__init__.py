# Personal fork - added search_limiter for custom search functionality
from .rate_limiter import RateLimiter, api_limiter, comment_limiter

# Custom rate limiter for search endpoints
search_limiter = RateLimiter(max_calls=10, period=60)

__all__ = ["RateLimiter", "api_limiter", "comment_limiter", "search_limiter"]
