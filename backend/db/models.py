from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    provider = Column(String) # e.g., "google"

class Goal(Base):
    __tablename__ = "goals"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    is_completed = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    steps = relationship("GoalStep", back_populates="goal")

class GoalStep(Base):
    __tablename__ = "goal_steps"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String)
    is_completed = Column(Boolean, default=False)
    goal_id = Column(Integer, ForeignKey("goals.id"))
    
    goal = relationship("Goal", back_populates="steps")