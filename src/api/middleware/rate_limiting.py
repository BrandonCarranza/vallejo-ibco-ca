"""
API rate limiting middleware.

Implements graduated rate limiting:
- Public tier: 100 requests/hour (no authentication)
- Researcher tier: 1000 requests/hour (with JWT token)
- Burst protection: 20 requests/10 seconds (all tiers)

Uses Redis for distributed rate limit tracking.
"""

import time
from typing import Optional, Tuple

import redis
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.config.logging_config import get_logger
from src.config.settings import settings

logger = get_logger(__name__)


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, limit_type: str, retry_after: int):
        self.limit_type = limit_type
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded: {limit_type}")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using Redis backend.

    Implements sliding window rate limiting with separate limits for:
    - Hourly requests (public vs. researcher tier)
    - Burst requests (10-second window)
    """

    # Rate limit configurations
    PUBLIC_HOURLY_LIMIT = 100  # requests per hour for unauthenticated users
    RESEARCHER_HOURLY_LIMIT = 1000  # requests per hour for authenticated users
    BURST_LIMIT = 20  # requests per 10 seconds (all users)
    BURST_WINDOW = 10  # seconds

    # Redis key prefixes
    HOURLY_KEY_PREFIX = "ratelimit:hourly:"
    BURST_KEY_PREFIX = "ratelimit:burst:"

    def __init__(self, app, redis_client: Optional[redis.Redis] = None):
        """
        Initialize rate limit middleware.

        Args:
            app: FastAPI application
            redis_client: Optional Redis client (will create if not provided)
        """
        super().__init__(app)

        # Initialize Redis client
        if redis_client:
            self.redis = redis_client
        else:
            self.redis = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )

        logger.info("Rate limiting middleware initialized")

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        # Skip rate limiting for certain paths
        if self._should_skip_rate_limit(request):
            return await call_next(request)

        try:
            # Get client identifier and tier
            client_id = self._get_client_identifier(request)
            tier = self._get_rate_limit_tier(request)

            # Check rate limits
            self._check_hourly_limit(client_id, tier)
            self._check_burst_limit(client_id)

            # Process request
            response = await call_next(request)

            # Add rate limit headers to response
            self._add_rate_limit_headers(response, client_id, tier)

            return response

        except RateLimitExceeded as e:
            # Log rate limit exceeded
            logger.warning(
                f"Rate limit exceeded for {client_id}",
                extra={
                    "client_id": client_id,
                    "limit_type": e.limit_type,
                    "retry_after": e.retry_after,
                    "path": request.url.path,
                },
            )

            # Return 429 Too Many Requests
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "rate_limit_exceeded",
                    "message": f"Rate limit exceeded: {e.limit_type}",
                    "retry_after": e.retry_after,
                    "documentation": "https://docs.ibco-ca.us/api/rate-limits",
                },
                headers={"Retry-After": str(e.retry_after)},
            )

        except redis.RedisError as e:
            # Log Redis error but allow request (fail open)
            logger.error(
                f"Redis error in rate limiting: {e}",
                exc_info=True,
                extra={"path": request.url.path},
            )
            return await call_next(request)

    def _should_skip_rate_limit(self, request: Request) -> bool:
        """
        Determine if rate limiting should be skipped for this request.

        Args:
            request: FastAPI request

        Returns:
            True if rate limiting should be skipped
        """
        path = request.url.path

        # Skip for health check, metrics, and admin endpoints
        skip_paths = [
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]

        return any(path.startswith(skip_path) for skip_path in skip_paths)

    def _get_client_identifier(self, request: Request) -> str:
        """
        Get unique identifier for the client.

        Uses JWT sub claim if authenticated, otherwise IP address.

        Args:
            request: FastAPI request

        Returns:
            Client identifier string
        """
        # Check for authenticated user (JWT sub claim in request state)
        if hasattr(request.state, "user") and request.state.user:
            return f"user:{request.state.user.get('sub', 'unknown')}"

        # Fall back to IP address
        # Check X-Forwarded-For header (for proxied requests)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take first IP in the chain
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        return f"ip:{client_ip}"

    def _get_rate_limit_tier(self, request: Request) -> str:
        """
        Determine rate limit tier for the request.

        Args:
            request: FastAPI request

        Returns:
            Rate limit tier ("public" or "researcher")
        """
        # Check if user is authenticated with researcher tier
        if hasattr(request.state, "user") and request.state.user:
            tier = request.state.user.get("tier", "public")
            return tier if tier in ["public", "researcher"] else "public"

        return "public"

    def _check_hourly_limit(self, client_id: str, tier: str) -> None:
        """
        Check hourly rate limit.

        Args:
            client_id: Client identifier
            tier: Rate limit tier

        Raises:
            RateLimitExceeded: If hourly limit exceeded
        """
        # Get limit for tier
        limit = (
            self.RESEARCHER_HOURLY_LIMIT if tier == "researcher" else self.PUBLIC_HOURLY_LIMIT
        )

        # Redis key for this client's hourly counter
        current_hour = int(time.time() / 3600)
        key = f"{self.HOURLY_KEY_PREFIX}{client_id}:{current_hour}"

        # Increment counter
        try:
            current = self.redis.incr(key)

            # Set expiration on first increment (2 hours to allow for cleanup)
            if current == 1:
                self.redis.expire(key, 7200)

            # Check if limit exceeded
            if current > limit:
                retry_after = 3600 - (int(time.time()) % 3600)  # Seconds until next hour
                raise RateLimitExceeded(
                    limit_type=f"hourly ({limit} requests/hour for {tier} tier)",
                    retry_after=retry_after,
                )

        except redis.RedisError:
            # Fail open on Redis errors
            logger.error("Redis error checking hourly limit", exc_info=True)

    def _check_burst_limit(self, client_id: str) -> None:
        """
        Check burst rate limit (sliding window).

        Args:
            client_id: Client identifier

        Raises:
            RateLimitExceeded: If burst limit exceeded
        """
        current_time = time.time()
        window_start = current_time - self.BURST_WINDOW

        # Redis key for this client's burst counter
        key = f"{self.BURST_KEY_PREFIX}{client_id}"

        try:
            # Use sorted set to track request timestamps
            pipe = self.redis.pipeline()

            # Remove old timestamps outside the window
            pipe.zremrangebyscore(key, 0, window_start)

            # Add current timestamp
            pipe.zadd(key, {str(current_time): current_time})

            # Count requests in window
            pipe.zcount(key, window_start, current_time)

            # Set expiration
            pipe.expire(key, self.BURST_WINDOW * 2)

            results = pipe.execute()
            count = results[2]  # Result from zcount

            # Check if burst limit exceeded
            if count > self.BURST_LIMIT:
                raise RateLimitExceeded(
                    limit_type=f"burst ({self.BURST_LIMIT} requests/{self.BURST_WINDOW} seconds)",
                    retry_after=self.BURST_WINDOW,
                )

        except redis.RedisError:
            # Fail open on Redis errors
            logger.error("Redis error checking burst limit", exc_info=True)

    def _add_rate_limit_headers(
        self, response: Response, client_id: str, tier: str
    ) -> None:
        """
        Add rate limit headers to response.

        Args:
            response: FastAPI response
            client_id: Client identifier
            tier: Rate limit tier
        """
        try:
            # Get limit for tier
            limit = (
                self.RESEARCHER_HOURLY_LIMIT
                if tier == "researcher"
                else self.PUBLIC_HOURLY_LIMIT
            )

            # Get current usage
            current_hour = int(time.time() / 3600)
            key = f"{self.HOURLY_KEY_PREFIX}{client_id}:{current_hour}"
            current = int(self.redis.get(key) or 0)

            # Add headers
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(max(0, limit - current))
            response.headers["X-RateLimit-Reset"] = str(
                (current_hour + 1) * 3600
            )  # Unix timestamp

        except redis.RedisError:
            # Don't fail request if we can't add headers
            logger.error("Redis error adding rate limit headers", exc_info=True)

    def get_rate_limit_status(self, client_id: str, tier: str) -> dict:
        """
        Get current rate limit status for a client.

        Args:
            client_id: Client identifier
            tier: Rate limit tier

        Returns:
            Dictionary with rate limit status
        """
        limit = (
            self.RESEARCHER_HOURLY_LIMIT if tier == "researcher" else self.PUBLIC_HOURLY_LIMIT
        )

        current_hour = int(time.time() / 3600)
        key = f"{self.HOURLY_KEY_PREFIX}{client_id}:{current_hour}"

        try:
            current = int(self.redis.get(key) or 0)
            return {
                "tier": tier,
                "hourly_limit": limit,
                "hourly_used": current,
                "hourly_remaining": max(0, limit - current),
                "reset_at": (current_hour + 1) * 3600,
                "burst_limit": self.BURST_LIMIT,
                "burst_window_seconds": self.BURST_WINDOW,
            }
        except redis.RedisError as e:
            logger.error(f"Redis error getting rate limit status: {e}")
            return {
                "tier": tier,
                "hourly_limit": limit,
                "error": "Unable to fetch current usage",
            }
