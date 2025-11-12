"""
JWT token authentication for API access.

Supports two tiers:
- Public (read-only): Basic API access
- Researcher: Bulk export endpoints, higher rate limits

Tokens are long-lived (1 year) for accessibility.
Revocation is supported via Redis blacklist.
"""

import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional

import jwt
import redis
from pydantic import BaseModel

from src.config.logging_config import get_logger
from src.config.settings import settings

logger = get_logger(__name__)


class TokenTier(str):
    """Token tier constants."""

    PUBLIC = "public"
    RESEARCHER = "researcher"


class TokenMetadata(BaseModel):
    """Metadata for an issued token."""

    token_id: str
    user_id: str
    tier: str
    purpose: str
    contact_email: str
    organization: Optional[str] = None
    issued_at: datetime
    expires_at: datetime
    revoked: bool = False
    revoked_at: Optional[datetime] = None
    revoke_reason: Optional[str] = None


class TokenManager:
    """
    Manages JWT token generation, validation, and revocation.

    Uses Redis for token blacklist (revoked tokens).
    """

    # Token settings
    TOKEN_ALGORITHM = "HS256"
    TOKEN_EXPIRATION_DAYS = 365  # 1 year
    BLACKLIST_KEY_PREFIX = "token:blacklist:"
    METADATA_KEY_PREFIX = "token:metadata:"

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialize token manager.

        Args:
            redis_client: Optional Redis client
        """
        if redis_client:
            self.redis = redis_client
        else:
            self.redis = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )

        self.secret_key = settings.secret_key
        logger.info("Token manager initialized")

    def generate_token(
        self,
        user_id: str,
        tier: str,
        purpose: str,
        contact_email: str,
        organization: Optional[str] = None,
        expiration_days: Optional[int] = None,
    ) -> tuple[str, TokenMetadata]:
        """
        Generate a new JWT token.

        Args:
            user_id: Unique identifier for the user/requestor
            tier: Token tier ("public" or "researcher")
            purpose: Purpose of the token (e.g., "Research project on municipal finance")
            contact_email: Email contact for the token holder
            organization: Optional organization name
            expiration_days: Optional custom expiration (default: 365 days)

        Returns:
            Tuple of (JWT token string, TokenMetadata)
        """
        # Generate unique token ID
        token_id = self._generate_token_id()

        # Calculate expiration
        expiration_days = expiration_days or self.TOKEN_EXPIRATION_DAYS
        issued_at = datetime.utcnow()
        expires_at = issued_at + timedelta(days=expiration_days)

        # Create JWT payload
        payload = {
            "jti": token_id,  # JWT ID
            "sub": user_id,  # Subject (user identifier)
            "tier": tier,  # Rate limit tier
            "iat": int(issued_at.timestamp()),  # Issued at
            "exp": int(expires_at.timestamp()),  # Expiration
            "purpose": purpose,
        }

        # Encode JWT
        token = jwt.encode(payload, self.secret_key, algorithm=self.TOKEN_ALGORITHM)

        # Store metadata in Redis
        metadata = TokenMetadata(
            token_id=token_id,
            user_id=user_id,
            tier=tier,
            purpose=purpose,
            contact_email=contact_email,
            organization=organization,
            issued_at=issued_at,
            expires_at=expires_at,
        )

        self._store_metadata(metadata)

        logger.info(
            f"Generated {tier} token for {user_id}",
            extra={
                "token_id": token_id,
                "user_id": user_id,
                "tier": tier,
                "expires_at": expires_at.isoformat(),
            },
        )

        return token, metadata

    def validate_token(self, token: str) -> Optional[Dict]:
        """
        Validate JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded token payload if valid, None otherwise
        """
        try:
            # Decode and verify token
            payload = jwt.decode(
                token, self.secret_key, algorithms=[self.TOKEN_ALGORITHM]
            )

            # Check if token is blacklisted
            token_id = payload.get("jti")
            if self._is_blacklisted(token_id):
                logger.warning(
                    f"Attempted use of revoked token: {token_id}",
                    extra={"token_id": token_id},
                )
                return None

            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("Token validation failed: expired")
            return None

        except jwt.InvalidTokenError as e:
            logger.warning(f"Token validation failed: {e}")
            return None

    def revoke_token(self, token_id: str, reason: str = "Revoked by administrator") -> bool:
        """
        Revoke a token by adding it to the blacklist.

        Args:
            token_id: Token ID (jti claim) to revoke
            reason: Reason for revocation

        Returns:
            True if revoked successfully, False otherwise
        """
        try:
            # Add to blacklist (set with 2-year TTL to eventually expire)
            blacklist_key = f"{self.BLACKLIST_KEY_PREFIX}{token_id}"
            self.redis.setex(blacklist_key, 2 * 365 * 24 * 3600, reason)

            # Update metadata
            metadata_key = f"{self.METADATA_KEY_PREFIX}{token_id}"
            metadata_json = self.redis.get(metadata_key)

            if metadata_json:
                import json

                metadata = json.loads(metadata_json)
                metadata["revoked"] = True
                metadata["revoked_at"] = datetime.utcnow().isoformat()
                metadata["revoke_reason"] = reason
                self.redis.set(metadata_key, json.dumps(metadata))

            logger.info(
                f"Revoked token {token_id}",
                extra={"token_id": token_id, "reason": reason},
            )

            return True

        except redis.RedisError as e:
            logger.error(f"Failed to revoke token {token_id}: {e}", exc_info=True)
            return False

    def get_token_metadata(self, token_id: str) -> Optional[TokenMetadata]:
        """
        Get metadata for a token.

        Args:
            token_id: Token ID

        Returns:
            TokenMetadata if found, None otherwise
        """
        try:
            import json

            metadata_key = f"{self.METADATA_KEY_PREFIX}{token_id}"
            metadata_json = self.redis.get(metadata_key)

            if metadata_json:
                metadata_dict = json.loads(metadata_json)
                return TokenMetadata(**metadata_dict)

            return None

        except (redis.RedisError, json.JSONDecodeError) as e:
            logger.error(f"Failed to get token metadata: {e}", exc_info=True)
            return None

    def list_active_tokens(self) -> list[TokenMetadata]:
        """
        List all active (non-revoked) tokens.

        Returns:
            List of TokenMetadata for active tokens
        """
        try:
            import json

            # Scan for all metadata keys
            pattern = f"{self.METADATA_KEY_PREFIX}*"
            tokens = []

            for key in self.redis.scan_iter(pattern):
                metadata_json = self.redis.get(key)
                if metadata_json:
                    metadata_dict = json.loads(metadata_json)
                    metadata = TokenMetadata(**metadata_dict)

                    # Include only non-revoked tokens
                    if not metadata.revoked:
                        tokens.append(metadata)

            return tokens

        except (redis.RedisError, json.JSONDecodeError) as e:
            logger.error(f"Failed to list tokens: {e}", exc_info=True)
            return []

    def _generate_token_id(self) -> str:
        """Generate unique token ID."""
        return secrets.token_urlsafe(32)

    def _is_blacklisted(self, token_id: str) -> bool:
        """
        Check if token is blacklisted.

        Args:
            token_id: Token ID

        Returns:
            True if blacklisted, False otherwise
        """
        try:
            blacklist_key = f"{self.BLACKLIST_KEY_PREFIX}{token_id}"
            return self.redis.exists(blacklist_key) > 0
        except redis.RedisError:
            # Fail open (allow token if Redis is down)
            logger.error("Redis error checking blacklist", exc_info=True)
            return False

    def _store_metadata(self, metadata: TokenMetadata) -> None:
        """
        Store token metadata in Redis.

        Args:
            metadata: TokenMetadata to store
        """
        try:
            import json

            metadata_key = f"{self.METADATA_KEY_PREFIX}{metadata.token_id}"
            metadata_dict = metadata.model_dump()

            # Convert datetime objects to ISO strings
            for key, value in metadata_dict.items():
                if isinstance(value, datetime):
                    metadata_dict[key] = value.isoformat()

            self.redis.set(metadata_key, json.dumps(metadata_dict))

        except redis.RedisError as e:
            logger.error(f"Failed to store token metadata: {e}", exc_info=True)


# Global token manager instance
_token_manager: Optional[TokenManager] = None


def get_token_manager() -> TokenManager:
    """Get global token manager instance."""
    global _token_manager
    if _token_manager is None:
        _token_manager = TokenManager()
    return _token_manager
