# synapse-api/core/security.py

from fastapi import HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from auth.service import AuthService
from core.db import get_db
from auth.models import UserProfile # Need to import UserProfile for type hinting
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> UserProfile: # Added type hint for clarity
    """
    Dependency to get current authenticated user from JWT token (Synapse Session JWT)
    """
    try:
        auth_service = AuthService(db)
        # Verifies the Synapse Session JWT
        user = await auth_service.verify_token(credentials.credentials) 
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    
    except Exception as e:
        logger.error(f"Authentication error (Session JWT): {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """
    Optional authentication - returns None if no valid token
    """
    try:
        # Note: This will correctly fail and return None if no token is present
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


# --- NEW AUTHENTICATION DEPENDENCY FOR AGENT GATEWAY ---
async def get_current_user_from_privy_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> UserProfile:
    """
    Dependency to get the current authenticated user by verifying the raw Privy Token.
    Used by the agent to POST strategies.
    """
    try:
        auth_service = AuthService(db)
        
        # CRITICAL CHANGE: Verify the raw Privy Token, which handles user creation/lookup
        user = await auth_service.verify_privy_token(credentials.credentials)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Privy token.",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return user
        
    except Exception as e:
        logger.error(f"Authentication error (Privy Token): {str(e)}")
        # Use 403 Forbidden to clearly indicate that authentication failed 
        # specifically for this endpoint's expected token type.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Privy Token validation failed.",
            headers={"WWW-Authenticate": "Bearer"},
        )