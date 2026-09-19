# backend/app/tasks.py
import os
import asyncio
from celery import Celery
from backend.app.agents.orchestrator import BidOrchestrator

redis_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

celery_app = Celery(
    "rfp_tasks",
    broker=redis_url,
    backend=result_backend
)

@celery_app.task
def process_rfp_background(file_path: str, company_id: str):
    """
    Celery task to process the RFP.
    Wrapper to run the async orchestrator pipeline inside a sync Celery worker.
    """
    orchestrator = BidOrchestrator()
    
    async def run_pipeline():
        async for update in orchestrator.generate_bid_streaming(file_path, company_id):
            # In a full system, broadcast these events via Websockets or Redis PubSub.
            # Draining the generator to let the side-effects (DB save) happen.
            pass
            
    try:
        asyncio.run(run_pipeline())
        return {"status": "success", "file": file_path}
    except Exception as e:
        return {"status": "error", "error": str(e)}
