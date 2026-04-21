# Personal fork - added search_limiter for custom search functionality
from .rate_limiter import RateLimiter, api_limiter, comment_limiter

# Custom rate limiter for search endpoints
# Reduced to 5 calls/60s to avoid hitting upstream API limits on my account
search_limiter = RateLimiter(max_calls=5, period=60)

__all__ = ["RateLimiter", "api_limiter", "comment_limiter", "search_limiter"]
