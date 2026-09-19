# backend/app/models/project.py
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, JSON, Float, Integer, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from backend.app.models.base import Base


class PastProject(Base):
    __tablename__ = "past_projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    
    name = Column(String, nullable=False)
    description = Column(String)
    tech_stack = Column(JSON, default=[])  # List of technologies
    
    # Timeline data
    timeline_estimated = Column(Integer)  # weeks
    timeline_actual = Column(Integer)     # weeks
    
    # Cost data
    cost_estimated = Column(Float)
    cost_actual = Column(Float)
    
    # Team
    team_size = Column(Integer)
    
    # Lessons
    lessons_learned = Column(String)
    challenges = Column(JSON, default=[])
    success_factors = Column(JSON, default=[])
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    company = relationship("Company", back_populates="past_projects")