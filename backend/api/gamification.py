from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from backend.auth.users import current_active_user
from backend.db.models import User, UserProfile, Goal, SubGoal, GoalTask, GoalStatus
from backend.db.session import get_async_session
from backend.schemas import GoalRead, GoalRequest, TokenResponse
from backend.agents.service import AIAgent
from backend.services.gamification_engine import GamificationEngine

router = APIRouter()
agent = AIAgent()

@router.post("/goals", response_model=GoalRead)
async def create_goal(
    goal_in: GoalRequest,
    decompose: bool = False,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    # Create Base Goal with new fields
    new_goal = Goal(
        user_id=user.id,
        title=goal_in.title,
        description=goal_in.description,
        deadline=goal_in.deadline,      # Saved to DB
        days_per_week=goal_in.days_per_week # Saved to DB
    )
    db.add(new_goal)
    await db.commit()
    await db.refresh(new_goal)

    # Goal Decomposition
    if decompose:
        # Pass the deadline and schedule to the AI
        milestones = agent.generate_subgoals(
            goal_text=goal_in.title, 
            deadline=goal_in.deadline,
            days_per_week=goal_in.days_per_week
        )
        
        for m in milestones:
            # Create SubGoal (Milestone)
            sub = SubGoal(
                goal_id=new_goal.id,
                title=m["title"],
                # We can store the AI's "description" or "estimated_sessions" if we add those columns
                # For now, we map title -> title.
            )
            db.add(sub)
        
        await db.commit()
        await db.refresh(new_goal)

    return new_goal

@router.post("/use-token", response_model=TokenResponse)
async def use_token(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalars().first()
    
    if not profile:
        profile = UserProfile(user_id=user.id)
        db.add(profile)
    
    # Ensure initialized date
    if not profile.last_reset_date:
        profile.last_reset_date = datetime.now(timezone.utc)

    # Weekly Reset Check
    time_since_reset = datetime.now(timezone.utc) - profile.last_reset_date
    if time_since_reset.days >= 7:
        profile.weekly_tokens = 3
        profile.tokens_used = 0
        profile.last_reset_date = datetime.now(timezone.utc)
        
    # Deduction Logic
    if profile.weekly_tokens > 0:
        profile.weekly_tokens -= 1
        profile.tokens_used += 1
        await db.commit()
        return {"status": "success", "remaining": profile.weekly_tokens}
    else:
        raise HTTPException(status_code=403, detail="No tokens left!")

@router.post("/restart-week")
async def restart_week_route(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Triggers the AI replanning logic after a token failure.
    """
    # Inject the global 'agent' instance here
    response = await GamificationEngine.restart_week_smart(db, user.id, agent)
    return response