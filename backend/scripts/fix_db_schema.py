import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:12345678@localhost:5432/rfp_bidder_db")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("Checking and adding missing columns to bids table...")
    
    columns_to_add = [
        ("legal_compliance", "JSON")
    ]
    
    for col_name, col_type in columns_to_add:
        try:
            conn.execute(text(f"ALTER TABLE bids ADD COLUMN {col_name} {col_type};"))
            conn.commit()
            print(f"Added column: {col_name}")
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"Column {col_name} already exists.")
            else:
                print(f"Error adding {col_name}: {e}")

print("Migration complete.")
