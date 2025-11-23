from sqlalchemy.ext.asyncio import AsyncSession
from auth.repository import UserRepository
from auth.models import UserProfile
from providers.privy import PrivyProvider
from core.errors import AuthenticationError
from datetime import datetime, timedelta
import jwt
from core.config import settings
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.privy = PrivyProvider()
    
    async def verify_privy_token(self, token: str) -> UserProfile:
        """
        Verify Privy token and return/create user profile
        """
        # Verify token with Privy
        claims = await self.privy.verify_token(token)
        if not claims:
            raise AuthenticationError("Invalid or expired token")
        
        # Extract user data
        user_data = self.privy.extract_user_data(claims)
        privy_user_id = user_data["privy_user_id"]
        
        if not privy_user_id:
            raise AuthenticationError("Invalid token: missing user ID")
        
        # Get or create user
        user = await self.user_repo.get_by_privy_id(privy_user_id)
        
        if not user:
            # Create new user
            user = await self.user_repo.create_user(
                privy_user_id=privy_user_id,
                email=user_data.get("email"),
                phone=user_data.get("phone"),
                last_login=datetime.utcnow()
            )
            
            # Add identities
            await self._sync_identities(user, user_data)
        else:
            # Update last login
            await self.user_repo.update_user(
                user.id,
                last_login=datetime.utcnow()
            )
        
        return user
    
    async def _sync_identities(self, user: UserProfile, user_data: Dict[str, Any]):
        """Sync user identities from Privy data"""
        # Add email identity
        if user_data.get("email"):
            await self.user_repo.add_identity(
                user.id,
                "email",
                user_data["email"],
                is_verified=True
            )
        
        # Add phone identity
        if user_data.get("phone"):
            await self.user_repo.add_identity(
                user.id,
                "phone",
                user_data["phone"],
                is_verified=True
            )
        
        # Add wallet identity
        if user_data.get("wallet_address"):
            await self.user_repo.add_identity(
                user.id,
                "wallet",
                user_data["wallet_address"],
                is_verified=True
            )
    
    def generate_session_token(self, user: UserProfile) -> str:
        """Generate JWT session token for user"""
        payload = {
            "user_id": str(user.id),
            "privy_user_id": user.privy_user_id,
            "exp": datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRE_HOURS),
            "iat": datetime.utcnow(),
        }
        
        # FIX: Force HS256 to ensure compatibility with string secret keys
        return jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm="HS256"
        )
    
    async def verify_token(self, token: str) -> Optional[UserProfile]:
        """Verify session JWT token and return user"""
        try:
            # FIX: Force HS256 to match the generation method
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=["HS256"]
            )
            
            privy_user_id = payload.get("privy_user_id")
            if not privy_user_id:
                return None
            
            user = await self.user_repo.get_by_privy_id(privy_user_id)
            return user
            
        except jwt.ExpiredSignatureError:
            logger.warning("Session token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid session token")
            return None