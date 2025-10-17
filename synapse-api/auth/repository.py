from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from auth.models import UserProfile, Identity
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_privy_id(self, privy_user_id: str) -> Optional[UserProfile]:
        """Get user by Privy user ID"""
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.privy_user_id == privy_user_id)
        )
        return result.scalar_one_or_none()
    
    async def create_user(self, privy_user_id: str, **kwargs) -> UserProfile:
        """Create new user profile"""
        user = UserProfile(privy_user_id=privy_user_id, **kwargs)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        logger.info(f"Created user profile for privy_id: {privy_user_id}")
        return user
    
    async def update_user(self, user_id: str, **kwargs) -> Optional[UserProfile]:
        """Update user profile"""
        await self.db.execute(
            update(UserProfile)
            .where(UserProfile.id == user_id)
            .values(**kwargs)
        )
        await self.db.commit()
        
        # Return updated user
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_identities(self, user_id: str) -> List[Identity]:
        """Get all identities for a user"""
        result = await self.db.execute(
            select(Identity).where(Identity.user_id == user_id)
        )
        return result.scalars().all()
    
    async def add_identity(self, user_id: str, identity_type: str, identity_value: str, **kwargs) -> Identity:
        """Add new identity to user"""
        identity = Identity(
            user_id=user_id,
            identity_type=identity_type,
            identity_value=identity_value,
            **kwargs
        )
        self.db.add(identity)
        await self.db.commit()
        await self.db.refresh(identity)
        logger.info(f"Added {identity_type} identity for user {user_id}")
        return identity