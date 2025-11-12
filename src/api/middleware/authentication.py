"""
JWT authentication middleware for API requests.

Validates Bearer tokens in Authorization header and adds user
information to request.state for downstream use.
"""

from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.api.auth.tokens import get_token_manager
from src.config.logging_config import get_logger

logger = get_logger(__name__)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    JWT authentication middleware.

    Validates JWT tokens from Authorization header and adds
    decoded token payload to request.state.user for use by
    rate limiting and endpoint authorization.
    """

    def __init__(self, app):
        """Initialize authentication middleware."""
        super().__init__(app)
        self.token_manager = get_token_manager()
        logger.info("Authentication middleware initialized")

    async def dispatch(self, request: Request, call_next):
        """Process request with authentication."""
        # Skip authentication for certain paths
        if self._should_skip_auth(request):
            return await call_next(request)

        # Extract token from Authorization header
        token = self._extract_token(request)

        if token:
            # Validate token
            payload = self.token_manager.validate_token(token)

            if payload:
                # Add user info to request state for downstream use
                request.state.user = payload
                logger.debug(
                    f"Authenticated request from {payload.get('sub')} ({payload.get('tier')} tier)",
                    extra={
                        "user_id": payload.get("sub"),
                        "tier": payload.get("tier"),
                        "token_id": payload.get("jti"),
                    },
                )
            else:
                # Invalid token - log warning but allow request
                # (will be treated as unauthenticated/public tier)
                logger.warning(
                    "Invalid token in Authorization header",
                    extra={"path": request.url.path},
                )
                request.state.user = None
        else:
            # No token provided - treat as public tier
            request.state.user = None

        # Process request
        response = await call_next(request)
        return response

    def _should_skip_auth(self, request: Request) -> bool:
        """
        Determine if authentication should be skipped for this request.

        Args:
            request: FastAPI request

        Returns:
            True if authentication should be skipped
        """
        path = request.url.path

        # Skip for public endpoints
        skip_paths = [
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]

        return any(path.startswith(skip_path) for skip_path in skip_paths)

    def _extract_token(self, request: Request) -> Optional[str]:
        """
        Extract JWT token from Authorization header.

        Expects format: "Authorization: Bearer <token>"

        Args:
            request: FastAPI request

        Returns:
            Token string if found, None otherwise
        """
        auth_header = request.headers.get("Authorization", "")

        if not auth_header:
            return None

        # Check for Bearer token format
        parts = auth_header.split()

        if len(parts) != 2:
            logger.warning(
                f"Invalid Authorization header format: expected 'Bearer <token>', got '{auth_header}'",
                extra={"path": request.url.path},
            )
            return None

        scheme, token = parts

        if scheme.lower() != "bearer":
            logger.warning(
                f"Unsupported authentication scheme: {scheme}",
                extra={"path": request.url.path},
            )
            return None

        return token
