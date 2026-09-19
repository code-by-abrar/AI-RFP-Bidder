# backend/app/models/employee.py
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Boolean, JSON, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.models.base import Base

class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    seniority = Column(String, nullable=False)
    skills = Column(JSON, nullable=True) # List of skills
    is_available = Column(Boolean, default=True) # true if on bench
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", back_populates="employees")
