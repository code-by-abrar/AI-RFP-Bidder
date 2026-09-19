# backend/app/models/bid.py

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, JSON, Float, Integer, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from backend.app.models.base import Base

class Bid(Base):
    __tablename__ = "bids"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    rfp_file_path = Column(String, nullable=False)
    rfp_extraction = Column(JSON, nullable=True)
    technical_proposal = Column(JSON, nullable=True)
    estimation = Column(JSON, nullable=True)
    legal_compliance = Column(JSON, nullable=True)
    go_no_go_decision = Column(JSON, nullable=True)
    allocated_team = Column(JSON, nullable=True)
    
    # Metadata
    status = Column(String, default="draft")  # draft, submitted, won, lost
    bid_amount = Column(Float, nullable=True)
    bid_timeline_weeks = Column(Integer, nullable=True)
    confidence_score = Column(Float, default=0.0)  # 0.0-1.0
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    submitted_at = Column(DateTime, nullable=True)
    
    # Relations
    company = relationship("Company", back_populates="bids")
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "status": self.status,
            "bid_amount": self.bid_amount,
            "bid_timeline_weeks": self.bid_timeline_weeks,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "rfp_extraction": self.rfp_extraction,
            "go_no_go_decision": self.go_no_go_decision,
            "technical_proposal": self.technical_proposal,
            "estimation": self.estimation,
            "allocated_team": self.allocated_team,
            "legal_compliance": self.legal_compliance,
        }

