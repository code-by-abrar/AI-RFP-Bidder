# backend/app/agents/agent5_legal_compliance.py

import json
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from backend.app.agents.agent1_rfp_parser import RFPExtraction
from backend.app.agents.agent3_tech_proposal import TechProposal
from backend.app.services.llm_service import LLMService
from backend.app.utils.prompts import SYSTEM_PROMPTS, PROMPT_TEMPLATES

logger = logging.getLogger(__name__)

class Finding(BaseModel):
    category: str
    issue: str
    severity: str
    impact: str

class ComplianceStatus(BaseModel):
    gdpr: str
    data_security: str
    ip_ownership: str

class LegalComplianceResult(BaseModel):
    risk_level: str
    findings: List[Finding]
    compliance_status: ComplianceStatus
    mitigation_suggestions: List[str]
    overall_summary: str

class LegalComplianceAgent:
    def __init__(self):
        self.llm_service = LLMService()
    
    async def check_compliance(
        self,
        rfp_data: RFPExtraction,
        proposal: TechProposal
    ) -> LegalComplianceResult:
        """Analyze RFP and proposal for legal/compliance risks"""
        
        logger.info(f"Checking compliance for: {rfp_data.project_title}")
        
        # Prepare context
        requirements_context = self._format_requirements_context(rfp_data)
        proposal_context = self._format_proposal_context(proposal)
        
        # Call LLM
        prompt = PROMPT_TEMPLATES["CHECK_COMPLIANCE"](
            requirements_context,
            proposal_context
        )
        
        response = await self.llm_service.call_llm_json(
            system_prompt=SYSTEM_PROMPTS["LEGAL_EXPERT"],
            user_prompt=prompt,
            response_schema=LegalComplianceResult.model_json_schema()
        )
        
        # Parse and validate
        result = LegalComplianceResult(**response)
        
        logger.info("Compliance check completed")
        return result
    
    def _format_requirements_context(self, rfp: RFPExtraction) -> str:
        """Format RFP requirements for legal analysis"""
        return f"""
Project: {rfp.project_title}
Industry: {rfp.industry}
Compliance Requirements: {json.dumps(rfp.compliance_requirements, indent=2)}
Constraints: {json.dumps(rfp.constraints, indent=2)}
Deliverables: {json.dumps(rfp.deliverables, indent=2)}
        """.strip()
    
    def _format_proposal_context(self, proposal: TechProposal) -> str:
        """Format technical proposal for legal analysis"""
        return f"""
Executive Summary: {proposal.executive_summary}
Tech Stack: {json.dumps(proposal.tech_stack.model_dump(), indent=2)}
Security Measures: {json.dumps(proposal.security_measures, indent=2)}
Deployment Strategy: {proposal.deployment_strategy.ci_cd_pipeline}
        """.strip()
