from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Depends
from fastapi.responses import StreamingResponse, FileResponse
import json
import os
from backend.app.agents.orchestrator import BidOrchestrator
from backend.app.middleware.auth import get_current_user
from backend.app.services.db_service import DatabaseService
from backend.app.services.export_service import DocumentExportService
from backend.app.models.bid import Bid

router = APIRouter(prefix="/api/bid", tags=["Bid"])
db = DatabaseService()

@router.post("/")
async def create_bid(
    bid_data: dict,
    current_user = Depends(get_current_user)
):
    """Save bid draft"""
    bid = Bid(
        company_id=current_user.company_id,
        **bid_data
    )
    await db.save_bid(bid)
    return bid.to_dict()

@router.get("/")
async def get_bids(current_user = Depends(get_current_user)):
    """Get all bids for company"""
    bids = await db.get_bids_by_company(current_user.company_id)
    return [b.to_dict() for b in bids]

@router.get("/{bid_id}")
async def get_bid(
    bid_id: str,
    current_user = Depends(get_current_user)
):
    """Get single bid detail"""
    bid = await db.get_bid_by_id(bid_id)
    if not bid or str(bid.company_id) != str(current_user.company_id):
        raise HTTPException(status_code=404, detail="Bid not found")
    return bid.to_dict()

@router.put("/{bid_id}")
async def update_bid(
    bid_id: str,
    bid_data: dict,
    current_user = Depends(get_current_user)
):
    """Update bid"""
    bid = await db.get_bid_by_id(bid_id)
    if not bid or bid.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    for key, value in bid_data.items():
        setattr(bid, key, value)
    
    await db.save_bid(bid)
    return bid.to_dict()

@router.get("/{bid_id}/export")
async def export_bid(
    bid_id: str,
    current_user = Depends(get_current_user)
):
    """Export bid as a Word document"""
    bid = await db.get_bid_by_id(bid_id)
    if not bid or str(bid.company_id) != str(current_user.company_id):
        raise HTTPException(status_code=404, detail="Bid not found")
        
    try:
        file_path = DocumentExportService.generate_word_document(bid.to_dict())
        return FileResponse(
            file_path, 
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
            filename=f"Proposal_{bid_id}.docx"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate document: {str(e)}")