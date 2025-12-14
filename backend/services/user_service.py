from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.db.models import UserProfile

async def get_user_agent_config(db: AsyncSession, user_id: int) -> dict:
    """
    Retrieves the real user preferences from Postgres.
    Returns a default dict if no profile exists.
    """
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    profile = result.scalars().first()
    
    # Default Defaults
    defaults = {
        "mode": "productivity",
        "tone": "supportive",
        "refinement_level": "standard",
        "model": "gpt-4o"
    }
    
    if profile and profile.agent_preferences:
        # Merge DB prefs over defaults
        return {**defaults, **profile.agent_preferences}
    
    return defaults