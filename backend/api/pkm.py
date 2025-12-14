import os
import shutil
import aiofiles
from sqlalchemy import select
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader, UnstructuredEPubLoader

from backend.auth.users import current_active_user
from backend.db.models import User, UserProfile
from backend.schemas import SearchRequest
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
    req: SearchRequest,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session) # Inject DB
):
    # 1. Fetch User Profile for Preferences
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalars().first()
    
    # Default to empty dict if no profile
    user_prefs = profile.agent_preferences if profile else {}
    
    # 2. Determine Mode (Default to "productivity" if not set)
    selected_mode = user_prefs.get("mode", "productivity")
    
    # 3. Call Agent with BOTH user_id and the specific preferences
    # Pass the full user_prefs dict so the Agent can apply overrides (tone/refinement)
    answer = agent.query_with_context(
        query=req.query, 
        user_id=user.id, 
        mode=selected_mode,
        overrides=user_prefs
    )
    
    return {"answer": answer}