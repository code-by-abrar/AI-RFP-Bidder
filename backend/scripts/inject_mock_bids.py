import sys
import os
import uuid
import random
from datetime import datetime, timedelta

# Ensure the backend module can be found when run from terminal
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

def inject_bids():
    if not SessionLocal:
        print("Database connection not established. Check your DATABASE_URL.")
        return

    # Using the mock company_id from backend/app/middleware/auth.py
    company_id = uuid.UUID("00000000-0000-0000-0000-000000000002")
    db = SessionLocal()
    
    Base.metadata.create_all(bind=engine)
    
    print("Injecting 'lost' bids to bring win rate to 95%...")
    
    # Check current won vs lost
    won_count = db.query(Bid).filter(Bid.company_id == company_id, Bid.status == "won").count()
    lost_count = db.query(Bid).filter(Bid.company_id == company_id, Bid.status == "lost").count()
    
    print(f"Current Won: {won_count}, Current Lost: {lost_count}")
    
    if won_count == 0:
        print("There are no won bids. Cannot target 95% win rate.")
        return
        
    current_win_rate = won_count / (won_count + lost_count)
    print(f"Current Win Rate: {current_win_rate * 100}%")
    
    target_win_rate = 0.95
    # Target total resolved (won + lost)
    # won / total = 0.95 => total = won / 0.95
    target_total = won_count / target_win_rate
    target_lost = int(round(target_total - won_count))
    
    bids_to_add_count = target_lost - lost_count
    
    if bids_to_add_count <= 0:
        print(f"Win rate is already at or below 95%. No lost bids added.")
        return
        
    print(f"Adding {bids_to_add_count} lost bids to reach ~95% win rate.")
    
    bids_to_add = []
    
    # Add 'lost' bids
    for i in range(bids_to_add_count):
        bids_to_add.append(Bid(
            company_id=company_id,
            rfp_file_path=f"mock_rfp_lost_{i}_{uuid.uuid4().hex[:6]}.pdf",
            status="lost",
            bid_amount=random.uniform(20000, 50000), 
            bid_timeline_weeks=random.randint(4, 12),
            confidence_score=random.uniform(0.3, 0.6), # Lower confidence for lost bids
            created_at=dt.datetime.now(dt.timezone.utc) - timedelta(days=random.randint(1, 180)),
            rfp_extraction={"industry": random.choice(["FinTech", "Healthcare", "E-commerce", "AI/ML", "Cybersecurity", "Cloud"])}
        ))
        
    try:
        db.add_all(bids_to_add)
        db.commit()
        
        # Verify
        new_lost = db.query(Bid).filter(Bid.company_id == company_id, Bid.status == "lost").count()
        new_rate = won_count / (won_count + new_lost)
        print(f"Successfully injected! New Win Rate is {new_rate * 100:.1f}%")
        
    except Exception as e:
        db.rollback()
        print(f"An error occurred: {e}")
    finally:
        db.close()
    
if __name__ == "__main__":
    inject_bids()
