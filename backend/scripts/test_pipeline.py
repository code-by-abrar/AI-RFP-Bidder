import asyncio
import os
import sys
import json

# Add project root to sys.path
sys.path.append(os.getcwd())

from backend.app.agents.orchestrator import BidOrchestrator
from backend.app.services.db_service import DatabaseService

async def test_full_pipeline():
    print("Starting End-to-End Pipeline Test...")
    orchestrator = BidOrchestrator()
    
    # Mock the parser's PDF extraction to avoid needing a real PDF
    from unittest.mock import patch
    from backend.app.agents.agent1_rfp_parser import RFPParserAgent
    
    # Use a dummy company ID (the one we seeded)
    company_id = "00000000-0000-0000-0000-000000000002"
    
    # Create a dummy RFP text file (won't be read by the mock)
    dummy_rfp = "dummy_rfp.pdf"
    with open(dummy_rfp, "w") as f: f.write("dummy")

    with patch.object(RFPParserAgent, '_extract_text', return_value="""
        Project Title: Cloud Migration for Retailer
        Overview: We need to migrate our legacy monolith to AWS.
        Requirements:
        - Must use Python and Docker.
        - Need high scalability and CI/CD.
        - Timeline: 12-15 weeks.
        - Budget: $150,000.
    """):    
        try:
            print(f"Analyzing dummy RFP: {dummy_rfp}")
            async for update in orchestrator.generate_bid_streaming(dummy_rfp, company_id):
                status = update.get("status")
                progress = update.get("progress")
                message = update.get("message", "")
                
                print(f"[{progress}%] {status}: {message}")
                
                if status == "search_complete":
                    # Check if we found similar projects
                    print(f"RAG RESULT check: {message}")
                
                if status == "complete":
                    print("PIPELINE SUCCESS!")
                    # print(json.dumps(update["data"], indent=2))
                    
        except Exception as e:
            print(f"PIPELINE FAILED: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if os.path.exists(dummy_rfp):
                os.remove(dummy_rfp)

if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
