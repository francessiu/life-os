from fastapi_users import schemas
from typing import Optional, Literal
from pydantic import BaseModel, Field

class UserRead(schemas.BaseUser[int]):
    pass

class UserCreate(schemas.BaseUserCreate):
    full_name: Optional[str] = None

class UserUpdate(schemas.BaseUserUpdate):
    full_name: Optional[str] = None
    
class AgentConfig(BaseModel):
    """
    Defines the brain of a specific agent instance.
    """
    name: str
    model: Literal["gpt-4o", "gpt-3.5-turbo", "claude-3-opus", "gemini-pro"]
    temperature: float = Field(0.7, ge=0.0, le=1.0)
    system_prompt: str
    refinement_level: Optional[Literal["concise", "detailed", "bullet-points"]] = None