from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.db import Base
import uuid

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    privy_user_id = Column(String(255), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    username = Column(String(100), nullable=True)
    picture_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    preferences = Column(JSONB, default=dict, nullable=False)

    identities = relationship("Identity", back_populates="user", cascade="all, delete-orphan")

class Identity(Base):
    __tablename__ = "identities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    # Identity details
    identity_type = Column(String(50), nullable=False)  # 'wallet', 'email', 'phone', 'google', etc.
    identity_value = Column(String(500), nullable=False)  # address, email, phone number, etc.
    # Verification status
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    identity_metadata = Column(JSONB, default=dict)  # renamed from 'metadata'

    user = relationship("UserProfile", back_populates="identities")

    def __repr__(self):
        return f"<Identity(type={self.identity_type}, value={self.identity_value[:10]}...)>"