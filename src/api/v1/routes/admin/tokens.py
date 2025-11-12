"""
Admin endpoints for API token management.

Requires admin authentication (to be implemented).
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, EmailStr

from src.api.auth.tokens import TokenManager, TokenMetadata, TokenTier, get_token_manager
from src.config.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/tokens", tags=["Admin - Token Management"])


# =============================================================================
# Request/Response Models
# =============================================================================


class TokenCreateRequest(BaseModel):
    """Request to create a new API token."""

    user_id: str
    tier: str  # "public" or "researcher"
    purpose: str
    contact_email: EmailStr
    organization: Optional[str] = None
    expiration_days: Optional[int] = None


class TokenCreateResponse(BaseModel):
    """Response with newly created token."""

    token: str
    metadata: TokenMetadata


class TokenMetadataResponse(BaseModel):
    """Response with token metadata."""

    token_id: str
    user_id: str
    tier: str
    purpose: str
    contact_email: str
    organization: Optional[str]
    issued_at: str
    expires_at: str
    revoked: bool
    revoked_at: Optional[str]
    revoke_reason: Optional[str]


class TokenRevokeRequest(BaseModel):
    """Request to revoke a token."""

    reason: str = "Revoked by administrator"


class TokenListResponse(BaseModel):
    """Response with list of tokens."""

    total: int
    tokens: List[TokenMetadataResponse]


# =============================================================================
# Endpoints
# =============================================================================


@router.post(
    "",
    response_model=TokenCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new API token",
)
async def create_token(request: TokenCreateRequest):
    """
    Create a new API token.

    **Tier Options:**
    - `public`: 100 requests/hour, read-only access
    - `researcher`: 1000 requests/hour, bulk export access

    **Example:**
    ```json
    {
      "user_id": "researcher@university.edu",
      "tier": "researcher",
      "purpose": "Municipal finance research project",
      "contact_email": "researcher@university.edu",
      "organization": "UC Berkeley"
    }
    ```
    """
    try:
        # Validate tier
        if request.tier not in [TokenTier.PUBLIC, TokenTier.RESEARCHER]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid tier. Must be '{TokenTier.PUBLIC}' or '{TokenTier.RESEARCHER}'",
            )

        # Generate token
        token_manager = get_token_manager()
        token, metadata = token_manager.generate_token(
            user_id=request.user_id,
            tier=request.tier,
            purpose=request.purpose,
            contact_email=request.contact_email,
            organization=request.organization,
            expiration_days=request.expiration_days,
        )

        logger.info(
            f"Admin created {request.tier} token for {request.user_id}",
            extra={"token_id": metadata.token_id},
        )

        return TokenCreateResponse(token=token, metadata=metadata)

    except Exception as e:
        logger.error(f"Failed to create token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create token",
        )


@router.get(
    "",
    response_model=TokenListResponse,
    summary="List all active tokens",
)
async def list_tokens(
    tier: Optional[str] = Query(None, description="Filter by tier (public/researcher)"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
):
    """
    List all active (non-revoked) API tokens.

    **Filters:**
    - `tier`: Filter by token tier (public/researcher)
    - `user_id`: Filter by user identifier

    Returns token metadata without the actual token value.
    """
    try:
        token_manager = get_token_manager()
        tokens = token_manager.list_active_tokens()

        # Apply filters
        if tier:
            tokens = [t for t in tokens if t.tier == tier]

        if user_id:
            tokens = [t for t in tokens if t.user_id == user_id]

        # Convert to response format
        token_responses = [
            TokenMetadataResponse(
                token_id=t.token_id,
                user_id=t.user_id,
                tier=t.tier,
                purpose=t.purpose,
                contact_email=t.contact_email,
                organization=t.organization,
                issued_at=t.issued_at.isoformat(),
                expires_at=t.expires_at.isoformat(),
                revoked=t.revoked,
                revoked_at=t.revoked_at.isoformat() if t.revoked_at else None,
                revoke_reason=t.revoke_reason,
            )
            for t in tokens
        ]

        return TokenListResponse(total=len(token_responses), tokens=token_responses)

    except Exception as e:
        logger.error(f"Failed to list tokens: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list tokens",
        )


@router.get(
    "/{token_id}",
    response_model=TokenMetadataResponse,
    summary="Get token details",
)
async def get_token(token_id: str):
    """
    Get metadata for a specific token by ID.

    Does not return the actual token value (tokens are not retrievable after creation).
    """
    try:
        token_manager = get_token_manager()
        metadata = token_manager.get_token_metadata(token_id)

        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Token {token_id} not found",
            )

        return TokenMetadataResponse(
            token_id=metadata.token_id,
            user_id=metadata.user_id,
            tier=metadata.tier,
            purpose=metadata.purpose,
            contact_email=metadata.contact_email,
            organization=metadata.organization,
            issued_at=metadata.issued_at.isoformat(),
            expires_at=metadata.expires_at.isoformat(),
            revoked=metadata.revoked,
            revoked_at=metadata.revoked_at.isoformat() if metadata.revoked_at else None,
            revoke_reason=metadata.revoke_reason,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get token metadata: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get token metadata",
        )


@router.post(
    "/{token_id}/revoke",
    status_code=status.HTTP_200_OK,
    summary="Revoke API token",
)
async def revoke_token(token_id: str, request: TokenRevokeRequest):
    """
    Revoke an API token by adding it to the blacklist.

    Revoked tokens will immediately fail authentication checks.
    Revocation is permanent and cannot be undone.

    **Example:**
    ```json
    {
      "reason": "User requested revocation"
    }
    ```
    """
    try:
        token_manager = get_token_manager()

        # Check if token exists
        metadata = token_manager.get_token_metadata(token_id)
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Token {token_id} not found",
            )

        # Check if already revoked
        if metadata.revoked:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Token {token_id} is already revoked",
            )

        # Revoke token
        success = token_manager.revoke_token(token_id, request.reason)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to revoke token",
            )

        logger.info(
            f"Admin revoked token {token_id}",
            extra={"token_id": token_id, "reason": request.reason},
        )

        return {
            "message": "Token revoked successfully",
            "token_id": token_id,
            "reason": request.reason,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to revoke token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke token",
        )


@router.get(
    "/{token_id}/validate",
    summary="Validate token status",
)
async def validate_token_status(token_id: str):
    """
    Check if a token ID is valid and active.

    Returns validation status without requiring the actual token.
    Useful for checking token status by ID.
    """
    try:
        token_manager = get_token_manager()
        metadata = token_manager.get_token_metadata(token_id)

        if not metadata:
            return {
                "valid": False,
                "reason": "Token not found",
            }

        if metadata.revoked:
            return {
                "valid": False,
                "reason": "Token has been revoked",
                "revoked_at": metadata.revoked_at.isoformat() if metadata.revoked_at else None,
                "revoke_reason": metadata.revoke_reason,
            }

        # Check expiration
        from datetime import datetime

        if datetime.utcnow() > metadata.expires_at:
            return {
                "valid": False,
                "reason": "Token has expired",
                "expired_at": metadata.expires_at.isoformat(),
            }

        return {
            "valid": True,
            "token_id": token_id,
            "user_id": metadata.user_id,
            "tier": metadata.tier,
            "expires_at": metadata.expires_at.isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to validate token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate token",
        )
