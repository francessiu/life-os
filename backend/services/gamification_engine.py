from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timedelta

from backend.db.models import UserProfile, Goal, SubGoal, GoalTask, GoalStatus

class GamificationEngine:
    
    @staticmethod
    async def get_or_create_profile(db: AsyncSession, user_id: int) -> UserProfile:
        result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        profile = result.scalars().first()
        if not profile:
            profile = UserProfile(user_id=user_id)
            db.add(profile)
            await db.commit()
            await db.refresh(profile)
        return profile

    @staticmethod
    async def process_weekly_reset(db: AsyncSession, user_id: int):
        """
        Checks if 7 days have passed. If so, resets tokens to 3.
        """
        profile = await GamificationEngine.get_or_create_profile(db, user_id)
        
        if not profile.last_reset_date:
            profile.last_reset_date = datetime.utcnow()
            await db.commit()
            return

        days_diff = (datetime.utcnow() - profile.last_reset_date).days
        
        if days_diff >= 7:
            profile.weekly_tokens = 3
            profile.tokens_used = 0
            profile.last_reset_date = datetime.utcnow()
            db.add(profile)
            await db.commit()

    @staticmethod
    async def use_token(db: AsyncSession, user_id: int) -> dict:
        """
        Handles token deduction and failure logic.
        """
        # 1. Check for Weekly Reset first
        await GamificationEngine.process_weekly_reset(db, user_id)
        
        profile = await GamificationEngine.get_or_create_profile(db, user_id)
        
        if profile.weekly_tokens > 0:
            profile.weekly_tokens -= 1
            profile.tokens_used += 1
            db.add(profile)
            await db.commit()
            return {"success": True, "remaining": profile.weekly_tokens, "message": "Token used"}
        
        else:
            # F-3.7: Token Limit Exceeded -> RESTART PLAN
            await GamificationEngine.fail_current_week(db, user_id)
            return {
                "success": False, 
                "remaining": 0, 
                "message": "Out of tokens! Current week's plan has failed. You must restart."
            }

    @staticmethod
    async def fail_current_week(db: AsyncSession, user_id: int):
        """
        Marks all active goals as FAILED when tokens run out.
        """
        # Find all active goals for this user
        result = await db.execute(
            select(Goal).where(
                Goal.user_id == user_id, 
                Goal.status == GoalStatus.ACTIVE
            )
        )
        active_goals = result.scalars().all()
        
        for goal in active_goals:
            goal.status = GoalStatus.FAILED
            db.add(goal)
            
        await db.commit()

    @staticmethod
    async def restart_week(db: AsyncSession, user_id: int, agent_service):
        """
        1. Identifies FAILED tasks in the current active SubGoal.
        2. Archives the failed attempts.
        3. Calls AI to break them down into easier steps.
        4. Resets Status to ACTIVE.
        """
        # 1. Get the Failed Goal & SubGoal
        # (Simplified query for demo: getting active goal's current subgoal)
        # In production, track "current_weekly_subgoal_id" in UserProfile
        
        result = await db.execute(
            select(SubGoal)
            .join(Goal)
            .where(Goal.user_id == user_id, Goal.status == GoalStatus.FAILED)
        )
        failed_subgoals = result.scalars().all()
        
        if not failed_subgoals:
            return {"message": "No failed goals to restart."}

        for subgoal in failed_subgoals:
            # 2. Identify Progress
            # We keep 'is_completed=True' tasks alone!
            
            result_tasks = await db.execute(
                select(GoalTask).where(
                    GoalTask.subgoal_id == subgoal.id,
                    GoalTask.is_completed == False # Only get what they FAILED
                )
            )
            failed_tasks = result_tasks.scalars().all()
            
            if not failed_tasks:
                continue # They finished everything? Then why is goal failed? (Edge case)

            failed_descriptions = [t.description for t in failed_tasks]
            
            # 3. AI Replanning (The "Smart" part)
            new_micro_tasks = agent_service.replan_week(failed_descriptions)
            
            # 4. Database Updates
            # Option A: Delete old failed tasks (cleaner UI)
            for old_task in failed_tasks:
                await db.delete(old_task)
            
            # Option B: Mark them as "Abandoned" if want to preserve history (better for analytics)
            # for old_task in failed_tasks:
            #    old_task.is_completed = False 
            #    old_task.description = f"[Failed] {old_task.description}"
            
            # 5. Insert New Micro-Tasks
            for micro_task in new_micro_tasks:
                new_task_db = GoalTask(
                    subgoal_id=subgoal.id,
                    description=micro_task, # The easier version
                    is_completed=False,
                    was_failed_previously=True # Flag this so UI can show "Retry" badge
                )
                db.add(new_task_db)
            
            # 6. Reset Goal Status
            subgoal.goal.status = GoalStatus.ACTIVE
            
        await db.commit()
        return {"status": "replan_complete", "message": "Plan adapted. Tasks broken down."}