import os
import shutil
import aiofiles
from sqlalchemy import select
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader, UnstructuredEPubLoader

from backend.auth.users import current_active_user
from backend.services.user_service import get_user_agent_config
from backend.db.models import User, UserProfile
from backend.schemas import ChatRequest
from backend.agents.service import AIAgent

router = APIRouter()
agent = AIAgent()

async def save_upload_file_tmp(upload_file: UploadFile) -> str:
    try:
        temp_dir = "temp_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, upload_file.filename)
        async with aiofiles.open(file_path, 'wb') as out_file:
            while content := await upload_file.read(1024):  
                await out_file.write(content)
        return file_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")

@router.post("/ingest")
async def ingest_document(
    file: UploadFile = File(...), 
    user: User = Depends(current_active_user)
):
    file_path = await save_upload_file_tmp(file)
    try:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext == ".pdf": loader = PyPDFLoader(file_path)
        elif ext == ".docx": loader = Docx2txtLoader(file_path)
        elif ext == ".epub": loader = UnstructuredEPubLoader(file_path)
        elif ext in [".txt", ".md", ".csv"]: loader = TextLoader(file_path)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported: {ext}")
            
        documents = loader.load()
        full_text = "\n\n".join([doc.page_content for doc in documents])
        
        # Call the Agent/RAG Service
        count = agent.rag.ingest_text(full_text, source=file.filename, user_id=user.id)
        
        return {"status": "success", "chunks": count, "filename": file.filename}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(file_path): os.remove(file_path)
    
@router.post("/chat")
async def chat_with_pkm(
    req: ChatRequest,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session) # Inject DB
):
    """
    Main Chat Endpoint.
    Handles RAG, Web Search Fallback, and Multi-Model Routing.
    """
    # 1. Fetch User Profile for Preferences
    user_prefs = await get_user_agent_config(db, user.id)
    
    # 2. Merge Request Overrides
    # Allow user to switch to a different LLM model for this one message
    overrides = user_prefs.copy()
    if req.model_provider:
        overrides["provider"] = req.model_provider
    if req.model_name:
        overrides["model"] = req.model_name

    # 3. Determine Mode
    # Priority: Request Mode > User Default Mode > "auto"
    selected_mode = req.mode 
    if selected_mode == "auto" and overrides.get("default_mode"):
        selected_mode = overrides.get("default_mode")
    
    # 3. Call Agent with BOTH user_id and the specific preferences
    # The agent will use 'selected_mode' to pick the personality (System Prompt), and overrides to pick the Brain (Provider/Model).
    try:
        answer = await agent.query_with_context(
            query=req.query, 
            user_id=user.id, 
            mode=selected_mode,
            overrides=overrides,
            db=db
        )
        return {"answer": answer, "mode_used": selected_mode}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent Error: {str(e)}")