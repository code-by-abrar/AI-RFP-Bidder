# backend/app/agents/agent1_rfp_parser.py
#  PDF se text nikal kar usay structured data (JSON) mein badalta hai.
import os
import json
import logging
from typing import Optional, Dict, List, Any
import pypdf
import pdfplumber
from pydantic import BaseModel, Field
from backend.app.services.llm_service import LLMService
from backend.app.utils.prompts import SYSTEM_PROMPTS, PROMPT_TEMPLATES

logger = logging.getLogger(__name__)

class TechRequirement(BaseModel):
    category: str = Field(..., description="e.g., Backend, Frontend, DevOps")
    technology: str = Field(..., description="e.g., Python, React, Docker")
    proficiency_level: str = Field(default="intermediate", description="junior, intermediate, expert")

class RFPExtraction(BaseModel):
    """Structured RFP extraction"""
    client_name: str
    industry: Optional[str]
    project_title: str
    project_description: str
    timeline: Dict[str, Any] = Field(
        default_factory=lambda: {"min_weeks": 0, "max_weeks": 0, "comment": ""}
    )
    budget: Dict[str, Any] = Field(
        default_factory=lambda: {"min": None, "max": None, "currency": "USD"}
    )
    tech_requirements: List[TechRequirement] = Field(default_factory=list)
    must_have_features: List[str] = Field(default_factory=list)
    nice_to_have_features: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    compliance_requirements: List[str] = Field(default_factory=list)
    integrations: List[str] = Field(default_factory=list)
    deliverables: List[str] = Field(default_factory=list)
    support_requirements: Optional[str] = None
    document_sections: Dict[str, str] = Field(default_factory=dict)

class RFPParserAgent:
    def __init__(self):
        self.llm_service = LLMService()
        
    async def parse_rfp(self, file_path: str) -> RFPExtraction:
        """Parse RFP document and extract structured data"""
        logger.info(f"Starting RFP parsing for: {file_path}")
        
        # Step 1: Extract text from PDF
        text = await self._extract_text(file_path)
        
        # Step 2: Identify sections
        sections = self._identify_sections(text)
        
        # Step 3: Extract structured data using LLM
        extraction = await self._extract_with_llm(text, sections)
        
        logger.info(f"RFP parsing completed. Found {len(extraction.must_have_features)} features")
        return extraction
    
    async def _extract_text(self, file_path: str) -> str:
        """Extract text from PDF using multiple methods for reliability"""
        text = ""
        
        try:
            # Method 1: Try pdfplumber (better for complex PDFs)
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
        except Exception as e:
            logger.warning(f"pdfplumber failed, trying pypdf: {e}")
            
            # Method 2: Fallback to pypdf
            with open(file_path, 'rb') as f:
                reader = pypdf.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() or ""
        
        if not text:
            raise ValueError("Could not extract text from PDF")
        
        return text
    
    def _identify_sections(self, text: str) -> Dict[str, str]:
        """Identify major sections in RFP"""
        sections = {}
        
        section_keywords = {
            "overview": ["executive summary", "overview", "introduction"],
            "scope": ["scope of work", "requirements", "deliverables"],
            "timeline": ["timeline", "schedule", "milestones"],
            "budget": ["budget", "pricing", "cost", "investment"],
            "technical": ["technical requirements", "technology", "platform"],
            "evaluation": ["evaluation criteria", "selection criteria"],
        }
        
        text_lower = text.lower()
        
        for section_name, keywords in section_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    # Find section content (next 2000 chars)
                    idx = text_lower.find(keyword)
                    sections[section_name] = text[idx:idx+2000]
                    break
        
        return sections
    
    async def _extract_with_llm(
        self, 
        text: str, 
        sections: Dict[str, str]
    ) -> RFPExtraction:
        """Use Claude to extract structured data"""
        
        # Limit text to first 60000 chars to avoid token limits (approx 15k tokens)
        limited_text = text[:60000]
        
        prompt = PROMPT_TEMPLATES["EXTRACT_RFP"](limited_text)
        
        response = await self.llm_service.call_llm_json(
            system_prompt=SYSTEM_PROMPTS["RFP_PARSER"],
            user_prompt=prompt,
            response_schema=RFPExtraction.model_json_schema()
        )
        
        # Parse and validate
        extraction = RFPExtraction(**response)
        
        return extraction