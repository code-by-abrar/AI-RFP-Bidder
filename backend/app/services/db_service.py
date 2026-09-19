# backend/app/services/db_service.py
import os
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.models.bid import Bid
from backend.app.models.knowledge import KnowledgeDocument
from dotenv import load_dotenv
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:12345678@localhost:5432/rfp_bidder_db")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

try:
    engine = create_engine(DATABASE_URL)
    
    # Import all models to ensure they are registered before creating tables
    from backend.app.models import Base
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    # If starting without DB, don't crash at import time
    engine = None
    SessionLocal = None

class DatabaseService:
    def __init__(self):
        pass
        
    async def get_bid_by_id(self, bid_id: str) -> Bid | None:
        if not SessionLocal: return None
        import uuid
        try:
            uuid.UUID(str(bid_id))
        except ValueError:
            return None
            
        def _get():
            with SessionLocal() as db:
                return db.query(Bid).filter(Bid.id == str(bid_id)).first()
        return await asyncio.to_thread(_get)
        
    async def get_project_by_id(self, project_id: str):
        if not SessionLocal: return None
        import uuid
        try:
            uuid.UUID(str(project_id))
        except ValueError:
            return None
            
        from backend.app.models.project import PastProject
        def _get():
            with SessionLocal() as db:
                return db.query(PastProject).filter(PastProject.id == str(project_id)).first()
        return await asyncio.to_thread(_get)
        
    async def get_bids_by_company(self, company_id: str) -> list[Bid]:
        if not SessionLocal: return []
        def _get():
            with SessionLocal() as db:
                return db.query(Bid).filter(Bid.company_id == str(company_id)).all()
        return await asyncio.to_thread(_get)
        
    async def save_bid(self, bid: Bid) -> Bid:
        if not SessionLocal: return bid
        def _save():
            with SessionLocal() as db:
                merged = db.merge(bid)
                db.commit()
                db.refresh(merged)
                return merged
        return await asyncio.to_thread(_save)

    async def get_knowledge_docs_by_company(self, company_id: str) -> list[KnowledgeDocument]:
        if not SessionLocal: return []
        def _get():
            with SessionLocal() as db:
                return db.query(KnowledgeDocument).filter(KnowledgeDocument.company_id == str(company_id)).all()
        return await asyncio.to_thread(_get)

    async def save_knowledge_doc(self, doc: KnowledgeDocument) -> KnowledgeDocument:
        if not SessionLocal: return doc
        def _save():
            with SessionLocal() as db:
                merged = db.merge(doc)
                db.commit()
                db.refresh(merged)
                return merged
        return await asyncio.to_thread(_save)
