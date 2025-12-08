from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
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

class GoalRequest(BaseModel):
    title: str

class SearchRequest(BaseModel):
    query: str

@app.get("/")
def read_root():
    """Simple check to confirm the root path is responsive."""
    return {"status": "LifeOS Brain is running", "version": "MVP"}

@app.post("/goals/decompose")
def decompose_goal(goal: GoalRequest):
    try:
        steps = agent.decompose_goal(goal.title)
        return {"goal": goal.title, "steps": steps}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pkm/ingest")
async def ingest_document(file: UploadFile = File(...)):
    """
    MVP: Upload a text file to index it.
    """
    content = await file.read()
    text = content.decode("utf-8")
    
    count = agent.rag.ingest_text(text, source=file.filename)
    return {"status": "success", "chunks_added": count}

@app.post("/pkm/chat")
def chat_with_pkm(req: SearchRequest):
    answer = agent.query_with_context(req.query)
    return {"answer": answer}