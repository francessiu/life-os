from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi_users import FastAPIUsers
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from pydantic import BaseModel
from typing import Optional, List

import shutil
import os
import aiofiles
from fastapi import UploadFile, File, HTTPException, Depends
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader, UnstructuredEPubLoader

from backend.auth.manager import get_user_manager
from backend.auth.oauth import google_oauth_client, microsoft_oauth_client
from backend.auth.backend import auth_backend
from backend.db.models import User, UserProfile
from backend.db.session import get_async_session
from backend.agents.service import AIAgent

app = FastAPI(title="LifeOS Brain")
agent = AIAgent()

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

# --- Authentication Setup ---
fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

current_active_user = fastapi_users.current_user(active=True)

# --- Authentication Route ---
app.include_router(
    fastapi_users.get_oauth_router(google_oauth_client, auth_backend, "SECRET"),
    prefix="/auth/google",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_oauth_router(microsoft_oauth_client, auth_backend, "SECRET"),
    prefix="/auth/microsoft",
    tags=["auth"],
)

# Protected routes
@app.get("/protected-route")
def protected_route(user: User = Depends(fastapi_users.current_user())):
    return {"message": f"Hello {user.email}"}

# --- Class ---
class GoalRequest(BaseModel):
    title: str
    description: Optional[str] = None
    # Optional: Allow user to override number of steps
    desired_steps: int = 5 

class StepResponse(BaseModel):
    step_order: int
    description: str
    is_completed: bool

class GoalResponse(BaseModel):
    id: Optional[int] = None
    title: str
    description: Optional[str]
    steps: List[StepResponse] = []

class TokenResponse(BaseModel):
    status: str
    remaining: int

class SearchRequest(BaseModel):
    query: str
    # Optional filters for the future feature
    limit: int = 3
    include_sources: bool = False

# --- Routes ---
@app.get("/")
def read_root():
    return {"status": "LifeOS Brain is running"}

@app.post("/goals/decompose")
def decompose_goal(goal: GoalRequest):
    try:
        steps = agent.decompose_goal(goal.title)
        return {"goal": goal.title, "steps": steps}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Helper function to save file temporarily
async def save_upload_file_tmp(upload_file: UploadFile) -> str:
    try:
        temp_dir = "temp_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        
        file_path = os.path.join(temp_dir, upload_file.filename)
        
        async with aiofiles.open(file_path, 'wb') as out_file:
            # Read in chunks to avoid memory overflow on large files
            while content := await upload_file.read(1024):  
                await out_file.write(content)
        return file_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")

@app.post("/pkm/ingest")
async def ingest_document(
    file: UploadFile = File(...), 
    user: User = Depends(current_active_user)
):
    # 1. Save file to disk temporarily
    file_path = await save_upload_file_tmp(file)
    documents = []
    
    try:
        # 2. Select the correct loader based on extension
        ext = os.path.splitext(file.filename)[1].lower()
        
        if ext == ".pdf":
            loader = PyPDFLoader(file_path)
        elif ext == ".docx":
            loader = Docx2txtLoader(file_path)
        elif ext == ".epub":
            loader = UnstructuredEPubLoader(file_path)
        elif ext in [".txt", ".md", ".csv"]:
            loader = TextLoader(file_path)
        else:
            # Fallback or Error
            os.remove(file_path)
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")
            
        # 3. Load text
        documents = loader.load()
        full_text = "\n\n".join([doc.page_content for doc in documents])
        
        # 4. Ingest into Vector DB
        # Note: We pass user.id (int) not the whole user object
        count = agent.rag.ingest_text(full_text, source=file.filename, user_id=user.id)
        
        return {
            "status": "success", 
            "chunks_added": count, 
            "user_id": user.id,
            "filename": file.filename
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
        
    finally:
        # 5. Cleanup: Always remove the temp file
        if os.path.exists(file_path):
            os.remove(file_path)

@app.post("/pkm/chat")
def chat_with_pkm(
    req: SearchRequest,
    user: User = Depends(current_active_user)
):
    # Pass real user.id to the agent
    answer = agent.query_with_context(req.query, user_id=user.id)
    return {"answer": answer}

@app.post("/agent/use-token", response_model=TokenResponse)
async def use_token(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    # Fetch the profile asynchronously
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalars().first()
    
    # If profile doesn't exist yet (first time user), create it
    if not profile:
        profile = UserProfile(user_id=user.id)
        db.add(profile)
        await db.commit()

    if not profile.last_reset_date:
        profile.last_reset_date = datetime.now(timezone.utc)
        db.add(profile)
        await db.commit()

    # --- Gamification Logic ---
    # Reset logic (if new week)
    time_since_reset = datetime.now(timezone.utc) - profile.last_reset_date
    if time_since_reset.days >= 7:
        profile.weekly_tokens = 3
        profile.tokens_used = 0
        profile.last_reset_date = datetime.now(timezone.utc)
        db.add(profile) # Ensure we save the reset
        await db.commit()
        
    if profile.weekly_tokens > 0:
        profile.weekly_tokens -= 1
        profile.tokens_used += 1
        await db.commit()
        return {"status": "success", "remaining": profile.weekly_tokens}
    else:
        raise HTTPException(status_code=403, detail="No tokens left!")
