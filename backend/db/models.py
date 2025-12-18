import enum
from fastapi_users.db import SQLAlchemyBaseUserTable, SQLAlchemyUserDatabase
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text, DateTime, JSON, Enum
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator
from fastapi import Depends
from datetime import datetime

from backend.db.session import get_async_session
from backend.db.session import Base

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
    __tablename__ = "user_profiles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), unique=True)
    
    # Gamification
    weekly_tokens = Column(Integer, default=3)
    tokens_used = Column(Integer, default=0)
    last_reset_date = Column(DateTime, default=datetime.utcnow)

    # Personalisation & Memory
    agent_preferences = Column(JSON, default={}) 
    
    # Feedback History
    # Stores: [{"query": "...", "timestamp": "..."}]
    interaction_history = Column(JSON, default=[])

    user = relationship("User", back_populates="profile")

class GoalStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed" # Used when tokens run out
    ARCHIVED = "archived"
    
class Goal(Base):
    __tablename__ = "goals"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    title = Column(String)
    status = Column(Enum(GoalStatus), default=GoalStatus.ACTIVE)
    deadline = Column(DateTime, nullable=True)
    days_per_week = Column(Integer, default=5)
    
    # Hierarchy: Goal -> SubGoals
    subgoals = relationship("SubGoal", back_populates="goal", cascade="all, delete-orphan")
    user = relationship("User", back_populates="goals")
    
class SubGoal(Base):
    """ Represents a Milestone or a Weekly Focus. """
    __tablename__ = "subgoals"
    id = Column(Integer, primary_key=True)
    goal_id = Column(Integer, ForeignKey("goals.id"))
    title = Column(String)
    is_completed = Column(Boolean, default=False)
    
    # Hierarchy: SubGoal -> Tasks
    tasks = relationship("GoalTask", back_populates="subgoal", cascade="all, delete-orphan")
    goal = relationship("Goal", back_populates="subgoals")

class GoalTask(Base):
    """
    The atomic unit. Completing these earns/preserves tokens.
    """
    __tablename__ = "goal_tasks"
    id = Column(Integer, primary_key=True)
    subgoal_id = Column(Integer, ForeignKey("subgoals.id"))
    
    description = Column(String)
    is_completed = Column(Boolean, default=False)
    
    # AI Metadata for Smart Restarts
    difficulty = Column(Integer, default=1) # 1-5, estimated by AI
    was_failed_previously = Column(Boolean, default=False) 

    subgoal = relationship("SubGoal", back_populates="tasks")

class SourceScope(str, enum.Enum):
    PRIVATE = "private" # Visible only to the owner
    GLOBAL = "global"   # Visible to all users (Shared Database)

class KnowledgeSource(Base):
    __tablename__ = "knowledge_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True) # Null if created by System Admin
    
    # Target Info
    url = Column(String, index=True, nullable=False)
    title = Column(String, nullable=True)
    scope = Column(Enum(SourceScope), default=SourceScope.PRIVATE)
    
    # Watcher Config
    is_active = Column(Boolean, default=True)
    update_frequency_hours = Column(Integer, default=24) # How often to re-crawl
    last_crawled_at = Column(DateTime, nullable=True)
    
    # Status
    error_count = Column(Integer, default=0)
    last_error = Column(String, nullable=True)

    user = relationship("User", back_populates="sources")
    
# Helper for FastAPI Users to access the DB
async def get_user_db(session: AsyncSession = Depends(get_async_session)): # Depends on your DB session maker
    yield SQLAlchemyUserDatabase(session, User, OAuthAccount)