# backend/app/agents/agent2_rag_search.py
# ye Knowledge Base search karta hai taake purane projects se seekh sake (RAG - Retrieval Augmented Generation
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np
import os
import chromadb
from sentence_transformers import SentenceTransformer
from sqlalchemy import select
from backend.app.models.project import PastProject
from backend.app.services.db_service import DatabaseService
from pydantic import BaseModel
import pypdf
import pdfplumber

logger = logging.getLogger(__name__)

class PastProjectData(BaseModel):
    id: str
    name: str
    tech_stack: List[str]
    timeline_estimated: int  # weeks
    timeline_actual: int     # weeks
    cost_estimated: float    # USD
    cost_actual: float       # USD
    team_size: int
    lessons_learned: str
    challenges: List[str]
    success_factors: List[str]

class HistoricalInsights(BaseModel):
    average_timeline: float
    timeline_variance: float
    average_cost: float
    cost_variance: float
    common_challenges: List[str]
    success_factors: List[str]

class KnowledgeHighlight(BaseModel):
    content: str
    source_file: str
    relevance_score: float

class RAGSearchAgent:
    def __init__(self):
        # Initialize embeddings model
        self.embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize ChromaDB
        db_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        self.collection = self.chroma_client.get_or_create_collection(name="rfp_embeddings")
        self.knowledge_collection = self.chroma_client.get_or_create_collection(name="company_knowledge")
        
        # Database service
        self.db = DatabaseService()
    
    async def ingest_past_projects(self, projects: List[PastProject]):
        """Ingest past projects into vector database"""
        logger.info(f"Ingesting {len(projects)} projects into vector DB")
        
        ids = []
        embeddings = []
        metadatas = []
        
        for project in projects:
            # Create document for embeddings
            doc_text = f"""
Project: {project.name}
Tech Stack: {', '.join(project.tech_stack)}
Timeline: {project.timeline_actual} weeks (estimated: {project.timeline_estimated})
Cost: ${project.cost_actual} (estimated: ${project.cost_estimated})
Team Size: {project.team_size}
Challenges: {', '.join(project.challenges)}
Lessons: {project.lessons_learned}
            """.strip()
            
            # Generate embeddings
            embedding = self.embeddings_model.encode(doc_text).tolist()
            
            # Prepare metadata
            ids.append(str(project.id))
            embeddings.append(embedding)
            metadatas.append({
                "project_id": str(project.id),
                "name": project.name,
                "tech_stack": ", ".join(project.tech_stack),
                "timeline_actual": project.timeline_actual,
                "cost_actual": project.cost_actual,
                "team_size": project.team_size,
            })
            
        # Batch insert to ChromaDB
        if ids:
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas
            )
        logger.info(f"Successfully ingested {len(ids)} projects")

    async def ingest_custom_document(self, file_path: str, company_id: str, doc_id: str, filename: str):
        """Extract text from file and ingest into knowledge collection"""
        logger.info(f"Ingesting custom document: {filename} (Type: {filename.split('.')[-1]})")
        
        # Check file size
        if os.path.getsize(file_path) == 0:
            raise ValueError("File is empty")
            
        text = ""
        ext = filename.split('.')[-1].lower()
        
        if ext == 'pdf':
            try:
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        text += page.extract_text() or ""
            except Exception as e:
                logger.warning(f"pdfplumber failed for {filename}: {e}")
                try:
                    with open(file_path, 'rb') as f:
                        reader = pypdf.PdfReader(f)
                        for page in reader.pages:
                            text += page.extract_text() or ""
                except Exception as e2:
                    logger.error(f"pypdf also failed for {filename}: {e2}")
                    raise ValueError(f"Could not extract text from PDF: {str(e2)}")
        elif ext == 'txt':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            except UnicodeDecodeError:
                with open(file_path, 'r', encoding='latin-1') as f:
                    text = f.read()
        else:
            raise ValueError(f"Unsupported file format for ingestion: {ext}")
        
        if not text.strip():
            raise ValueError("No text content found in document")
            
        # Chunk text (simple sliding window for now)
        chunks = [text[i:i+1000] for i in range(0, len(text), 800)]
        
        ids = []
        embeddings = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_{i}"
            embedding = self.embeddings_model.encode(chunk).tolist()
            ids.append(chunk_id)
            embeddings.append(embedding)
            metadatas.append({
                "doc_id": doc_id,
                "company_id": company_id,
                "filename": filename,
                "chunk_index": i
            })
            
        self.knowledge_collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=chunks
        )
        logger.info(f"Ingested {len(chunks)} chunks from {filename}")

    async def find_similar_projects(
        self, 
        rfp_requirements: str,
        company_id: str,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """Find similar past projects AND relevant knowledge base excerpts"""
        
        logger.info(f"Searching for {top_k} similar projects")
        
        # Generate embedding for RFP
        query_embedding = self.embeddings_model.encode(rfp_requirements).tolist()
        
        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["metadatas"]
        )
        
        # Fetch full project data from database
        similar_projects = []
        
        if results and results.get("metadatas") and len(results["metadatas"]) > 0:
            for metadata in results["metadatas"][0]:
                project_id = metadata["project_id"]
                
                project = await self.db.get_project_by_id(project_id)
                if project and str(project.company_id) == str(company_id):
                    similar_projects.append(PastProjectData(
                        id=str(project.id),
                        name=project.name,
                        tech_stack=project.tech_stack,
                        timeline_estimated=project.timeline_estimated,
                        timeline_actual=project.timeline_actual,
                        cost_estimated=project.cost_estimated,
                        cost_actual=project.cost_actual,
                        team_size=project.team_size,
                        lessons_learned=project.lessons_learned,
                        challenges=project.challenges,
                        success_factors=project.success_factors,
                    ))
        
        logger.info(f"Found {len(similar_projects)} relevant projects")
        
        # SEARCH KNOWLEDGE COLLECTION
        knowledge_results = self.knowledge_collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={"company_id": str(company_id)},
            include=["metadatas", "documents", "distances"]
        )
        
        highlights = []
        if knowledge_results and knowledge_results.get("documents") and len(knowledge_results["documents"]) > 0:
            for i in range(len(knowledge_results["documents"][0])):
                highlights.append(KnowledgeHighlight(
                    content=knowledge_results["documents"][0][i],
                    source_file=knowledge_results["metadatas"][0][i]["filename"],
                    relevance_score=float(1 - knowledge_results["distances"][0][i])
                ))
        
        return {
            "projects": similar_projects,
            "knowledge_highlights": highlights
        }
        
    async def query_knowledge_base(self, question: str, company_id: str, top_k: int = 3) -> str:
        """Search the knowledge base for a specific question to get context chunks (used by Questionnaire Filler)"""
        logger.info(f"Querying knowledge base for: {question[:50]}...")
        
        query_embedding = self.embeddings_model.encode(question).tolist()
        
        try:
            knowledge_results = self.knowledge_collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where={"company_id": str(company_id)},
                include=["documents"]
            )
            
            context = ""
            if knowledge_results and knowledge_results.get("documents") and len(knowledge_results["documents"]) > 0:
                doc_chunks = knowledge_results["documents"][0]
                context = "\n\n---\n\n".join(doc_chunks)
                
            return context
        except Exception as e:
            logger.error(f"Error querying knowledge base: {e}")
            return ""
    
    def extract_insights(self, projects: List[PastProjectData]) -> HistoricalInsights:
        """Extract statistical insights from similar projects"""
        
        if not projects:
            return HistoricalInsights(
                average_timeline=0,
                timeline_variance=0,
                average_cost=0,
                cost_variance=0,
                common_challenges=[],
                success_factors=[],
            )
        
        # Calculate timeline statistics
        timelines = [p.timeline_actual for p in projects]
        avg_timeline = np.mean(timelines)
        timeline_variance = np.std(timelines)
        
        # Calculate cost statistics
        costs = [p.cost_actual for p in projects]
        avg_cost = np.mean(costs)
        cost_variance = np.std(costs)
        
        # Extract common challenges
        all_challenges = []
        for p in projects:
            all_challenges.extend(p.challenges)
        
        from collections import Counter
        challenge_counts = Counter(all_challenges)
        common_challenges = [ch for ch, _ in challenge_counts.most_common(5)]
        
        # Extract success factors
        all_success_factors = []
        for p in projects:
            all_success_factors.extend(p.success_factors)
        
        success_factor_counts = Counter(all_success_factors)
        success_factors = [sf for sf, _ in success_factor_counts.most_common(5)]
        
        return HistoricalInsights(
            average_timeline=float(avg_timeline),
            timeline_variance=float(timeline_variance),
            average_cost=float(avg_cost),
            cost_variance=float(cost_variance),
            common_challenges=common_challenges,
            success_factors=success_factors,
        )