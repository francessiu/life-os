from fastapi_users.db import SQLAlchemyBaseUserTable, SQLAlchemyUserDatabase
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text, DateTime
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator
from fastapi import Depends
from datetime import datetime

Base = declarative_base()

# OAuth Account Table (Links User to Google/MS)
class OAuthAccount(Base):
    """
    Stores the tokens from Google/Microsoft so we can link them to a User.
    """
    __tablename__ = "oauth_account"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="cascade"), nullable=False)
    oauth_name = Column(String(100), index=True, nullable=False) # e.g., "google"
    access_token = Column(String(1024), nullable=False)
    expires_at = Column(Integer, nullable=True)
    refresh_token = Column(String(1024), nullable=True)
    account_id = Column(String(320), index=True, nullable=False) # The Google/MS user ID
    account_email = Column(String(320), nullable=False)

class User(SQLAlchemyBaseUserTable[int], Base):
    """
    The Master User Table.
    Inherits fields like email, hashed_password, is_active from SQLAlchemyBaseUserTable.
    """
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    
    # Relationships
    oauth_accounts = relationship("OAuthAccount", lazy="joined")
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    goals = relationship("Goal", back_populates="user")
    
class UserProfile(Base):
    """
    Separates 'Game Data' (Tokens, Streaks) from 'Identity Data'.
    """
    __tablename__ = "user_profiles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), unique=True)
    
    # Token Economy
    weekly_tokens = Column(Integer, default=3)
    tokens_used = Column(Integer, default=0)
    last_reset_date = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="profile")

class Goal(Base):
    __tablename__ = "goals"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text, nullable=True)
    is_completed = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("user.id"))
    
    user = relationship("User", back_populates="goals")
    steps = relationship("GoalStep", back_populates="goal")

class GoalStep(Base):
    __tablename__ = "goal_steps"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String)
    is_completed = Column(Boolean, default=False)
    goal_id = Column(Integer, ForeignKey("goals.id"))
    
    goal = relationship("Goal", back_populates="steps")
    
# Helper for FastAPI Users to access the DB
async def get_user_db(session: AsyncSession): # Depends on your DB session maker
    yield SQLAlchemyUserDatabase(session, User, OAuthAccount)