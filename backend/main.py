from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables from parent .env file
dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path)

from backend.app.routes.rfp_routes import router as rfp_router
from backend.app.routes.bid_routes import router as bid_router
from backend.app.routes.analytics_routes import router as analytics_router
from backend.app.routes.knowledge_routes import router as knowledge_router
from backend.app.routes.questionnaire_routes import router as questionnaire_router

app = FastAPI(title="AI RFP Bidder API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins, configure carefully in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(rfp_router)
app.include_router(bid_router)
app.include_router(analytics_router)
app.include_router(knowledge_router)
app.include_router(questionnaire_router)

# Mount the frontend directory as static files
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
else:
    print(f"Warning: Frontend directory not found at {frontend_path}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
