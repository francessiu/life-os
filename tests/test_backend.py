from fastapi.testclient import TestClient
from backend.app.main import app
import os

client = TestClient(app)

def test_root():
    """Check if the API is alive"""
    response = client.get("/")
    assert response.status_code == 200

def test_goal_decomposition():
    """Check if the Goal Agent returns steps"""
    payload = {"title": "Learn Python"}
    response = client.post("/goals/decompose", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["goal"] == "Learn to Surf"
    assert len(data["steps"]) == 5 # We mocked it to return 5 steps

def test_pkm_flow():
    """
    Full Integration Test:
    1. Upload a document (Ingest)
    2. Ask a question about it (Retrieval)
    """
    # 1. Ingest
    # We simulate a file upload
    file_content = b"LifeOS is a digital butler that helps you stay focused."
    files = {"file": ("manual.txt", file_content, "text/plain")}

    ingest_res = client.post("/pkm/ingest", files=files)
    assert ingest_res.status_code == 200
    assert ingest_res.json()["status"] == "success"

    # 2. Chat (Retrieval)
    # We ask a question that can only be answered by the text above
    chat_payload = {"query": "What does LifeOS help you do?"}
    chat_res = client.post("/pkm/chat", json=chat_payload)

    assert chat_res.status_code == 200
    answer = chat_res.json()["answer"]

    # Check if the AI mentions "focused" or "butler"
    print(f"\nAI Answer: {answer}")
    assert "focused" in answer.lower() or "butler" in answer.lower()