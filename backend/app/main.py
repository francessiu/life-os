from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from backend.api import preferences
from backend.core.config import settings
from backend.db.session import engine
from backend.db.models import Base

# Auth Imports
from backend.auth.users import fastapi_users
from backend.auth.backend import auth_backend
from backend.auth.oauth import google_oauth_client, microsoft_oauth_client, apple_oauth_client
from backend.auth.schemas import UserRead, UserCreate, UserUpdate
from backend.services.sync_service import sync_all_users

# API Router Imports
from backend.api import pkm, gamification

# Lifecycle: Ensure DB tables exist on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # In production, use Alembic for migrations instead of this
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="LifeOS Brain", lifespan=lifespan)
scheduler = AsyncIOScheduler()

# --- CORS Configuration ---
origins = [
    "http://localhost:3000",  # Your frontend URL
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows POST, GET, etc.
    allow_headers=["*"],
)

# --- ROUTER REGISTRATION ---
# 1. Standard Login (Email/Password)
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

# 2. Registration
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

# 3. Google OAuth Integration 
# This automatically handles the redirect to Google and the callback
app.include_router(
    fastapi_users.get_oauth_router(
        google_oauth_client,
        auth_backend,
        settings.SECRET_KEY,
        associate_by_email=True, # Links Google email to existing user account
    ),
    prefix="/auth/google",
    tags=["auth"],
)

# 4. Microsoft OAuth Integration 
app.include_router(
    fastapi_users.get_oauth_router(
        microsoft_oauth_client,
        auth_backend,
        settings.SECRET_KEY,
        associate_by_email=True,
    ),
    prefix="/auth/microsoft",
    tags=["auth"],
)

# 5. Apple OAuth Integration 
app.include_router(
    fastapi_users.get_oauth_router(
        apple_oauth_client,
        auth_backend,
        settings.SECRET_KEY,
        associate_by_email=True,
    ),
    prefix="/auth/apple",
    tags=["auth"],
)

# 6. User Profile Management
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

# --- 2. Feature Routes ---
app.include_router(pkm.router, prefix="/pkm", tags=["PKM"])
app.include_router(preferences.router, prefix="/preferences", tags=["Preferences"])
app.include_router(gamification.router, prefix="/agent", tags=["Gamification"])

@app.get("/")
def read_root():
    return {"status": "LifeOS Brain is running"}

@app.on_event("startup")
async def start_scheduler():
    scheduler.add_job(sync_all_users, 'interval', hours=1)
    scheduler.start()