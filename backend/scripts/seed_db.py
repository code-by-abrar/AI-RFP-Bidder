import asyncio
import os
import sys
import uuid
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.getcwd())

from backend.app.models.company import Company
from backend.app.models.project import PastProject
from backend.app.services.db_service import DatabaseService
from backend.app.agents.agent2_rag_search import RAGSearchAgent

async def seed_data():
    print("Starting database seeding...")
    db = DatabaseService()
    rag = RAGSearchAgent()
    
    # 1. Ensure a default company exists
    company_id = uuid.UUID("00000000-0000-0000-0000-000000000002")
    from backend.app.services.db_service import SessionLocal
    with SessionLocal() as session:
        company = session.query(Company).filter(Company.id == company_id).first()
        if not company:
            print(f"Creating mock company: {company_id}")
            company = Company(
                id=company_id,
                name="Nexus Bids Demo Corp",
                domain_name="nexusbids.ai"
            )
            session.add(company)
            session.commit()
    
    # 2. Define sample past projects
    sample_projects = [
        {
            "name": "Cloud Migration for Financial Services",
            "description": "Migrated a legacy banking system to AWS with zero downtime.",
            "tech_stack": ["Python", "AWS", "PostgreSQL", "Terraform", "Docker"],
            "timeline_estimated": 12,
            "timeline_actual": 14,
            "cost_estimated": 120000.0,
            "cost_actual": 145000.0,
            "team_size": 5,
            "lessons_learned": "Database migration took longer due to data cleanup needs.",
            "challenges": ["Data integrity issues", "Legacy API compatibility"],
            "success_factors": ["Strong CI/CD", "Expert DBAs"]
        },
        {
            "name": "E-Commerce Replatforming",
            "description": "Rebuilt a monolithic retail site using Next.js and Microservices.",
            "tech_stack": ["React", "Next.js", "Node.js", "MongoDB", "Kubernetes"],
            "timeline_estimated": 16,
            "timeline_actual": 16,
            "cost_estimated": 200000.0,
            "cost_actual": 195000.0,
            "team_size": 8,
            "lessons_learned": "Early integration testing saved us weeks of rework.",
            "challenges": ["Complex state management", "Third-party payment gateway bugs"],
            "success_factors": ["Headless architecture", "Automated testing"]
        },
        {
            "name": "AI-Powered Customer Support Portal",
            "description": "Implemented LLM-based chatbot for high-volume support desk.",
            "tech_stack": ["Python", "FastAPI", "Groq", "Pinecone", "React"],
            "timeline_estimated": 8,
            "timeline_actual": 10,
            "cost_estimated": 80000.0,
            "cost_actual": 95000.0,
            "team_size": 3,
            "lessons_learned": "Prompt engineering requires more iteration than software logic.",
            "challenges": ["LLM Hallucinations", "Latency requirements"],
            "success_factors": ["RAG architecture", "Stream processing"]
        }
    ]
    
    # 3. Save to Database and Ingest to Chroma
    with SessionLocal() as session:
        projects_to_ingest = []
        for p_data in sample_projects:
            # Check if exists
            existing = session.query(PastProject).filter(PastProject.name == p_data["name"]).first()
            if not existing:
                print(f"Adding project: {p_data['name']}")
                project = PastProject(
                    company_id=company_id,
                    **p_data
                )
                session.add(project)
                session.flush() # Get ID
                projects_to_ingest.append(project)
            else:
                print(f"Project already exists: {p_data['name']}")
                projects_to_ingest.append(existing)
        
        session.commit()
        
        # 4. Ingest into ChromaDB while session is still open/active
        print(f"Ingesting {len(projects_to_ingest)} projects into ChromaDB...")
        await rag.ingest_past_projects(projects_to_ingest)
    
    print("Seeding and Ingestion completed successfully!")

if __name__ == "__main__":
    asyncio.run(seed_data())
