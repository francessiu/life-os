import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta

from backend.app.main import app, current_active_user
from backend.db.models import User, UserProfile
from backend.db.session import async_session_maker, get_async_session
from backend.auth.manager import get_user_manager

# --- MOCK FIXTURES & UTILITIES ---

# Mock the database session for testing
@pytest.fixture
async def mock_db_session():
    """Provides a fresh, mocked AsyncSession for dependency override."""
    session = MagicMock(spec=AsyncSession)
    yield session

# Mock an authenticated user object
@pytest.fixture
def mock_user() -> User:
    """Returns a mock User object with a known ID."""
    return User(id=999, email="testuser@lifeos.dev")

# Override dependencies: Mock Authentication
@pytest.fixture(autouse=True)
def override_dependencies(mock_user, mock_db_session):
    """
    Overrides the Auth and DB dependencies globally for all tests.
    """
    app.dependency_overrides[current_active_user] = lambda: mock_user
    app.dependency_overrides[get_async_session] = lambda: mock_db_session
    yield
    app.dependency_overrides.clear()

# --- TEST CLIENT ---
@pytest.fixture
async def ac() -> AsyncClient:
    """Asynchronous client for testing FastAPI application."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

# --- TESTS ---
# Test 0: Check if LifeOS is running
@pytest.mark.asyncio
async def test_root(ac: AsyncClient):
    response = await ac.get("/")
    assert response.status_code == 200

# Test 1: Health Check
@pytest.mark.asyncio
async def test_read_root(ac: AsyncClient):
    """Test the basic root health check."""
    response = await ac.get("/")
    assert response.status_code == 200

# Test 2: AI Goal Decomposition
@pytest.mark.asyncio
@patch('backend.agents.service.AIAgent.decompose_goal')
async def test_goal_decomposition_success(mock_decompose_goal, ac: AsyncClient):
    """Test that the goal decomposition endpoint works and returns the mocked steps."""
    mock_decompose_goal.return_value = ["Step 1", "Step 2"] # Mock the LLM output directly
    payload = {"title": "Master Python Basics"}
    response = await ac.post("/goals/decompose", json=payload)
    assert response.status_code == 200
    assert len(response.json()["steps"]) == 2

# Test 3: PKM Ingestion
@pytest.mark.asyncio
@patch('backend.pkm.rag_service.RAGService.ingest_text')
@patch('backend.app.main.save_upload_file_tmp')
@patch('backend.app.main.TextLoader')
@patch('os.remove')
@patch('os.path.exists', return_value=True)
async def test_pkm_ingest_success(mock_exists, mock_remove, mock_loader_cls, mock_save_file, mock_ingest_text, ac: AsyncClient, mock_user):
    """Test file upload to ingestion pipeline."""

    mock_save_file.return_value = "/tmp/testfile.txt" # Mock file saving
    
    # Mock Loader to return dummy content
    mock_loader_instance = mock_loader_cls.return_value
    mock_loader_instance.load.return_value = [
        MagicMock(page_content="Financial report content.")
    ]
    
    mock_ingest_text.return_value = 10 # Mock RAG return
    
    file_content = b"Financial report content."
    
    response = await ac.post(
        "/pkm/ingest", 
        files={"file": ("report.txt", file_content, "text/plain")}
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    mock_remove.assert_called_once() # Verify cleanup was called

# Test 4: PKM Chat - Retrieval-Augmented Generation (Requires LLM Mock)
@pytest.mark.asyncio
@patch('backend.agents.service.AIAgent.query_with_context')
async def test_pkm_chat_retrieval(mock_query_with_context, ac: AsyncClient, mock_user):
    """Test that the chat endpoint calls the agent with the user's ID."""
    
    mock_query_with_context.return_value = "The answer is 42, according to your notes."
    
    payload = {"query": "What is the meaning of life?"}
    response = await ac.post("/pkm/chat", json=payload)
    
    assert response.status_code == 200
    assert "42" in response.json()["answer"]
    
    # Verify the agent was called with the user's multi-tenancy ID
    mock_query_with_context.assert_called_once()
    assert mock_query_with_context.call_args[1]['user_id'] == mock_user.id

# Test 5: Token Logic (Integration with Database Mock)
@pytest.mark.asyncio
async def test_token_logic_use_success(ac: AsyncClient, mock_db_session, mock_user):
    """Test successful token deduction."""
    
    # Mock the DB query result to return a profile with tokens
    mock_profile = UserProfile(user_id=mock_user.id, weekly_tokens=3, tokens_used=0, last_reset_date=datetime.now(timezone.utc))
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_profile
    mock_db_session.execute.return_value = mock_result
    
    response = await ac.post("/agent/use-token")
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "success"
    assert data["remaining"] == 2  # Should be 3 - 1 = 2
    
    # 3. Verify the commit happened (to save the token deduction)
    mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_token_logic_use_failure(ac: AsyncClient, mock_db_session, mock_user):
    """Test token use failure when tokens are zero."""
    
    # Mock the DB query result to return a profile with NO tokens
    mock_profile = UserProfile(user_id=mock_user.id, weekly_tokens=0, tokens_used=3, last_reset_date=datetime.now(timezone.utc))
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_profile
    mock_db_session.execute.return_value = mock_result
    
    response = await ac.post("/agent/use-token")
    
    assert response.status_code == 403
    assert "No tokens left!" in response.json()["detail"]
    
    # Verify that commit was NOT called
    mock_db_session.commit.assert_not_called()