from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified
from datetime import datetime

from backend.db.session import get_async_session
from backend.db.models import User, UserProfile
from backend.auth.users import current_active_user
from backend.schemas import UserPreferencesUpdate, FeedbackCreate, UserProfileResponse

router = APIRouter()

async def get_or_create_profile(db: AsyncSession, user_id: int) -> UserProfile:
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    profile = result.scalars().first()
    if not profile:
        profile = UserProfile(user_id=user_id, agent_preferences={})
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    return profile

@router.get("/", response_model=UserProfileResponse)
async def get_preferences(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Fetch current user settings."""
    profile = await get_or_create_profile(db, user.id)
    return profile

@router.patch("/", response_model=UserProfileResponse)
async def update_preferences(
    prefs: UserPreferencesUpdate,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Update agent personality/mode."""
    profile = await get_or_create_profile(db, user.id)
    
    # Update the JSON field safely
    current_prefs = dict(profile.agent_preferences) if profile.agent_preferences else {}
    
    if prefs.mode: current_prefs["mode"] = prefs.mode
    if prefs.tone: current_prefs["tone"] = prefs.tone
    if prefs.refinement_level: current_prefs["refinement_level"] = prefs.refinement_level
    
    profile.agent_preferences = current_prefs
    
    # Force SQLAlchemy to detect change in JSON field
    flag_modified(profile, "agent_preferences")
    
    await db.commit()
    await db.refresh(profile)
    return profile

@router.post("/feedback")
async def log_feedback(
    feedback: FeedbackCreate,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Log user feedback to improve future interactions.
    """
    profile = await get_or_create_profile(db, user.id)
    
    # Append new feedback entry
    entry = feedback.dict()
    entry["timestamp"] = datetime.utcnow().isoformat()
    
    current_history = list(profile.interaction_history) if profile.interaction_history else []
    current_history.append(entry)
    
    # Limit history size to prevent DB bloat (optional, e.g., last 50 items)
    if len(current_history) > 50:
        current_history.pop(0)
        
    profile.interaction_history = current_history
    flag_modified(profile, "interaction_history")
    
    await db.commit()
    
    # Placeholder: Trigger an async background task here to analyse feedback
    # and adjust specific preference weights automatically.
    
    return {"status": "recorded"}