import os
import sys
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.getcwd())

load_dotenv()
db_url = os.getenv("DATABASE_URL", "postgresql://postgres:12345678@localhost:5432/rfp_bidder_db")
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

print(f"Connecting to: {db_url}")
try:
    engine = create_engine(db_url)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Tables found: {tables}")
    
    if not tables:
        print("No tables found. Attempting to create them...")
        from backend.app.models import Base
        Base.metadata.create_all(engine)
        print("Tables created successfully.")
        print(f"Tables now: {inspector.get_table_names()}")
except Exception as e:
    print(f"Database error: {e}")
