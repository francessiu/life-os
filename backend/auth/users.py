from fastapi_users import FastAPIUsers
from backend.db.models import User
from backend.auth.manager import get_user_manager
from backend.auth.backend import auth_backend

# This 'fastapi_users' object is used to generate routers in main.py
fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

# A dependency to be used in other endpoints to get the logged-in user
current_active_user = fastapi_users.current_user(active=True)