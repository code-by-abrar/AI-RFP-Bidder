from fastapi import APIRouter, Depends
from backend.app.middleware.auth import get_current_user
from backend.app.services.db_service import DatabaseService
from collections import Counter

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])
db = DatabaseService()

@router.get("/stats")
async def get_stats(current_user = Depends(get_current_user)):
    """Get bid performance statistics for the company"""
    bids = await db.get_bids_by_company(current_user.company_id)
    
    total_bids = len(bids)
    status_counts = Counter(b.status for b in bids)
    
    # Calculate win rate
    won = status_counts.get("won", 0)
    lost = status_counts.get("lost", 0)
    submitted = status_counts.get("submitted", 0)
    draft = status_counts.get("draft", 0)
    
    win_rate = (won / (won + lost)) * 100 if (won + lost) > 0 else 0
    
    # Industry distribution
    industries = [b.rfp_extraction.get("industry", "Unknown") for b in bids if b.rfp_extraction]
    industry_counts = Counter(industries)
    
    # Monthly volume (dummy grouping for now, can be improved with real grouping)
    # Just return last 6 months counts or similar
    
    return {
        "total_proposals": total_bids,
        "win_rate": round(win_rate, 1),
        "status_distribution": {
            "won": won,
            "lost": lost,
            "submitted": submitted,
            "draft": draft
        },
        "industry_distribution": dict(industry_counts),
        "total_revenue": sum(b.bid_amount for b in bids if b.status == "won" and b.bid_amount)
    }
