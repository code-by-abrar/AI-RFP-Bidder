from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
import os
import logging
import shutil
from uuid import uuid4
from backend.app.middleware.auth import get_current_user
from backend.app.services.db_service import DatabaseService
from backend.app.models.knowledge import KnowledgeDocument
from backend.app.agents.agent2_rag_search import RAGSearchAgent

router = APIRouter(prefix="/api/knowledge", tags=["Knowledge Base"])
logger = logging.getLogger(__name__)
db = DatabaseService()
rag = RAGSearchAgent()

UPLOAD_DIR = "backend/uploads/knowledge"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    """Upload a document to the company's knowledge base"""
    if not file.filename.lower().endswith(('.pdf', '.docx', '.txt')):
        raise HTTPException(status_code=400, detail="Unsupported file format (Try PDF or TXT)")
    
    file_id = str(uuid4())
    ext = os.path.splitext(file.filename)[1]
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")
    
    # Save file
    content = await file.read()
    with open(file_path, "wb") as buffer:
        buffer.write(content)
    
    # Create DB record
    doc = KnowledgeDocument(
        id=uuid4(),
        company_id=current_user.company_id,
        filename=file.filename,
        file_path=file_path,
        document_type=ext.replace('.', '')
    )
    
    # Ingest into Vector DB
    # We'll call a method on RAGSearchAgent to process this file
    try:
        await rag.ingest_custom_document(file_path, str(current_user.company_id), str(doc.id), file.filename)
        await db.save_knowledge_doc(doc)
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        logger.error(f"Ingestion failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ingestion failed ({type(e).__name__}): {str(e)}")
    
    return doc.to_dict()

@router.get("/")
async def get_documents(current_user = Depends(get_current_user)):
    """Get all documents in the company's knowledge base"""
    docs = await db.get_knowledge_docs_by_company(current_user.company_id)
    return [d.to_dict() for d in docs]
