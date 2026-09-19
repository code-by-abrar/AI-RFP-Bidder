# backend/app/routes/rfp_routes.py

from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Depends
from fastapi.responses import StreamingResponse
import json
import os
from backend.app.agents.orchestrator import BidOrchestrator
from backend.app.middleware.auth import get_current_user
from backend.app.services.db_service import DatabaseService
from backend.app.models.bid import Bid

router = APIRouter(prefix="/api/rfp", tags=["RFP"])
orchestrator = BidOrchestrator()
db = DatabaseService()

@router.post("/analyze")
async def analyze_rfp(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    """
    Upload RFP and analyze it
    Returns streaming results
    """
    try:
        # Save file in a hidden directory to avoid uvicorn reload triggers
        file_path = f".data/uploads/{file.filename}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        async def generate():
            try:
                # Stream analysis results Phase 1
                async for update in orchestrator.start_bid_streaming(
                    file_path, 
                    current_user.company_id
                ):
                    yield json.dumps(update).encode() + b"\n"
            finally:
                # Cleanup
                if os.path.exists(file_path):
                    os.remove(file_path)
        
        return StreamingResponse(
            generate(),
            media_type="application/x-ndjson"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/{bid_id}")
async def get_analysis(
    bid_id: str,
    current_user = Depends(get_current_user)
):
    """Get saved bid analysis"""
    bid = await db.get_bid_by_id(bid_id)
    if not bid or bid.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    return bid.to_dict()

@router.post("/{bid_id}/continue")
async def continue_analysis(
    bid_id: str,
    current_user = Depends(get_current_user)
):
    """
    Resume analysis for a bid that required confirmation
    """
    async def generate():
        try:
            async for update in orchestrator.continue_bid_streaming(
                bid_id, 
                current_user.company_id
            ):
                yield json.dumps(update).encode() + b"\n"
        except Exception as e:
            yield json.dumps({"status": "error", "message": str(e)}).encode() + b"\n"
            
    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson"
    )
