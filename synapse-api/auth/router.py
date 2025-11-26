from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from auth.service import AuthService
from core.db import get_db
from core.security import get_current_user
from auth.models import UserProfile
from core.errors import AuthenticationError # Import AuthenticationError
import logging
import traceback # Keep traceback imported for logger.exception usage

logger = logging.getLogger(__name__)

# Note: Changing this router prefix from '/' to something more specific is usually best practice
router = APIRouter()


class VerifyTokenRequest(BaseModel):
    token: str


class AuthResponse(BaseModel):
    user_id: str
    privy_user_id: str
    email: str | None
    phone: str | None
    session_token: str


class UserProfileResponse(BaseModel):
    user_id: str
    privy_user_id: str
    email: str | None
    phone: str | None
    username: str | None
    created_at: str
    last_login: str | None
    preferences: dict


@router.post("/verify", response_model=AuthResponse)
async def verify_privy_token(
    request: VerifyTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify Privy token and return user profile with session token
    """
    try:
        auth_service = AuthService(db)
        
        # 1. Verify Privy token and retrieve/create user profile
        user = await auth_service.verify_privy_token(request.token)
        
        # 2. Generate session token
        session_token = auth_service.generate_session_token(user)
        
        logger.warning(f"[DEBUG] Session token for testing: {session_token}")
        logger.info(f"User login successful for user_id: {user.id}")
        
        return AuthResponse(
            user_id=str(user.id),
            privy_user_id=user.privy_user_id,
            email=user.email,
            phone=user.phone,
            session_token=session_token
        )
        
    except AuthenticationError as e:
        # Handle known authentication failures (e.g., invalid or expired Privy token)
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    except Exception as e:
        # Handle unexpected errors (e.g., database connection issues, PgBouncer issues)
        logger.exception(f"Unexpected error during user verification: {e}")
        
        # We don't need the specific SSL hint anymore since we fixed that in core/db.py
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected server error occurred during authentication."
        )


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Get current authenticated user profile
    """
    return UserProfileResponse(
        user_id=str(current_user.id),
        privy_user_id=current_user.privy_user_id,
        email=current_user.email,
        phone=current_user.phone,
        username=current_user.username,
        created_at=current_user.created_at.isoformat(),
        last_login=current_user.last_login.isoformat() if current_user.last_login else None,
        preferences=current_user.preferences or {}
    )


@router.post("/logout")
async def logout():
    """
    Logout endpoint (client should discard session token)
    """
    return {"message": "Logged out successfully"}