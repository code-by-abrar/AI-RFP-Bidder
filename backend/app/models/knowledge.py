from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from backend.app.models.base import Base

class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    document_type = Column(String, default="pdf")  # pdf, docx, txt
    
    # Metadata extracted during ingestion
    summary = Column(String, nullable=True)
    tags = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "filename": self.filename,
            "document_type": self.document_type,
            "summary": self.summary,
            "tags": self.tags,
            "created_at": self.created_at.isoformat()
        }
