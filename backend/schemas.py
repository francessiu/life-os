from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Dict, Any
from datetime import date, datetime

from backend.db.models import GoalStatus

# --- Goals ---
class GoalCreate(BaseModel):
    title: str
    description: Optional[str] = None
    metric_label: Optional[str] = None
    metric_target: Optional[int] = 0
    
class StepCreate(BaseModel):
    description: str
    step_order: int
    
class GoalRead(GoalCreate):
    id: int
    status: GoalStatus
    steps: List['StepRead'] = []
    class Config:
        orm_mode = True
        
GoalRead.update_forward_refs()

class StepRead(BaseModel):
    id: int
    description: str
    is_completed: bool
    step_order: int
    class Config:
        orm_mode = True

class GoalRequest(BaseModel):
    title: str
    description: Optional[str] = None
    
    # New Scheduling Constraints
    deadline: Optional[date] = None # YYYY-MM-DD
    days_per_week: int = Field(5, ge=1, le=7) # Defaults to 5 days a week

class GoalUpdate(BaseModel):
    title: Optional[str] = None
    metric_current: Optional[int] = None
    status: Optional[GoalStatus] = None

class StepResponse(BaseModel):
    step_order: int
    description: str
    is_completed: bool

class GoalResponse(BaseModel):
    id: Optional[int] = None
    title: str
    description: Optional[str]
    steps: List[StepResponse] = []

# --- Gamification ---
class TokenResponse(BaseModel):
    status: str
    remaining: int
    
# --- Chat & Agent Schemas ---
class ChatRequest(BaseModel):
    """The unified request object for the Chat Endpoint."""
    query: str
    
    # Mode Selection (e.g., "productivity", "academic", "casual", or "auto")
    mode: Optional[str] = "auto" 
    
    # Model Switching (Overrides user defaults if provided)
    # Examples: provider="openai", model="gpt-4o"
    model_provider: Optional[Literal["openai", "google", "anthropic"]] = None
    model_name: Optional[str] = None 
    
    # Optional: For debugging or specific constraints
    include_sources: bool = True

class AgentConfig(BaseModel):
    """Defines the configuration for a specific Agent personality."""
    name: str
    system_prompt: str
    
    # Brain Configuration
    provider: Literal["openai", "google", "anthropic"] = "openai"
    model: str = "gpt-4o"
    temperature: float = 0.7
    
    refinement_level: Optional[str] = None
    
# --- Personalisation ---
class UserPreferencesUpdate(BaseModel):
    """
    User defines how they want the agent to behave.
    """
    mode: Optional[str] = "productivity"   # matches presets keys
    tone: Optional[str] = None             # overrides preset
    refinement_level: Optional[str] = None # overrides preset

class FeedbackCreate(BaseModel):
    """
    User feedback on an agent response.
    """
    query: str
    response: str
    rating: int # 1-5
    comment: Optional[str] = None
    created_at: Optional[datetime] = None

class UserProfileResponse(BaseModel):
    weekly_tokens: int
    agent_preferences: Dict[str, Any]

class ResearchPlan(BaseModel):
    """Structured output from the Planner step."""
    explanation: str = Field(description="Brief explanation of the research strategy.")
    search_queries: List[str] = Field(description="List of 5-10 specific search queries to execute.")
    required_concepts: List[str] = Field(description="Key concepts or terms to look for.")