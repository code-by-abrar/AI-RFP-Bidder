import sys
import os
import uuid
import random
from datetime import datetime, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.app.services.db_service import SessionLocal, engine
from backend.app.models.base import Base
from backend.app.models.bid import Bid
from backend.app.models.employee import Employee
from backend.app.models.company import Company
from backend.app.models.user import User
from backend.app.models.knowledge import KnowledgeDocument
from backend.app.models.project import PastProject
import datetime as dt

def exact_95():
    if not SessionLocal: return
    company_id = uuid.UUID("00000000-0000-0000-0000-000000000002")
    db = SessionLocal()
    
    # We want exactly 57 won and 3 lost to make 57/60 = 0.95 (95.0%)
    current_won = db.query(Bid).filter(Bid.company_id == company_id, Bid.status == "won").count()
    current_lost = db.query(Bid).filter(Bid.company_id == company_id, Bid.status == "lost").count()
    
    # We need 57 won and 3 lost ideally.
    target_won = 57
    target_lost = 3
    
    bids = []
    
    if current_won < target_won:
        for i in range(target_won - current_won):
            bids.append(Bid(
                company_id=company_id,
                rfp_file_path=f"mock_rfp_won_exact_{i}.pdf",
                status="won",
                bid_amount=random.uniform(20000, 50000), 
                bid_timeline_weeks=random.randint(4, 12),
                created_at=dt.datetime.now(dt.timezone.utc) - timedelta(days=2)
            ))
            
    if current_lost < target_lost:
        for i in range(target_lost - current_lost):
            bids.append(Bid(
                company_id=company_id,
                rfp_file_path=f"mock_rfp_lost_exact_{i}.pdf",
                status="lost",
                bid_amount=random.uniform(20000, 50000), 
                bid_timeline_weeks=random.randint(4, 12),
                created_at=dt.datetime.now(dt.timezone.utc) - timedelta(days=2)
            ))
            
    if bids:
        db.add_all(bids)
        db.commit()
    
    new_won = db.query(Bid).filter(Bid.company_id == company_id, Bid.status == "won").count()
    new_lost = db.query(Bid).filter(Bid.company_id == company_id, Bid.status == "lost").count()
    print(f"Now doing exact math. Won: {new_won}, Lost: {new_lost}. Rate: {new_won/(new_won+new_lost)*100}%")
    db.close()

if __name__ == "__main__":
    exact_95()
