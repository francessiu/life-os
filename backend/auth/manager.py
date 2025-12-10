from typing import Optional
from fastapi import Request, Depends
from fastapi_users import BaseUserManager, IntegerIDMixin
from backend.db.models import User, get_user_db
from backend.core.config import settings

class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    reset_password_token_secret = settings.SECRET_KEY
    verification_token_secret = settings.SECRET_KEY

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")
        # Optional: Auto-create a UserProfile here if not using Database Triggers
        # But usually, it's safer to create it on first login or via a DB trigger.

async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)