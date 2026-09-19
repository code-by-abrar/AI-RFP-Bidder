# backend/app/agents/agent3_tech_proposal.py

import json
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from backend.app.agents.agent1_rfp_parser import RFPExtraction
from backend.app.agents.agent2_rag_search import PastProjectData, KnowledgeHighlight
from backend.app.services.llm_service import LLMService
from backend.app.utils.prompts import SYSTEM_PROMPTS, PROMPT_TEMPLATES

logger = logging.getLogger(__name__)

class DatabaseTable(BaseModel):
    name: str
    fields: List[Dict[str, Any]]
    indexes: List[str] = []
    description: Optional[str] = None

class DatabaseSchema(BaseModel):
    tables: List[DatabaseTable]
    relationships: List[Dict[str, str]] = []
    migration_strategy: Optional[str] = None

class TechStack(BaseModel):
    frontend: List[str] = []
    backend: List[str] = []
    database: List[str] = []
    infrastructure: List[str] = []
    devops: List[str] = []

class SystemArchitecture(BaseModel):
    diagram: str
    description: str
    components: List[Any]
    data_flow: Optional[str] = None

class APIEndpoint(BaseModel):
    method: str
    path: str
    description: str
    request_schema: Optional[Dict[str, Any]] = None
    response_schema: Optional[Dict[str, Any]] = None

class APIDesign(BaseModel):
    endpoints: List[APIEndpoint]
    authentication: str
    rate_limiting: Optional[str] = None

class DeploymentStrategy(BaseModel):
    ci_cd_pipeline: str
    environments: List[str]
    monitoring: List[str]
    backup_strategy: str
    disaster_recovery: Optional[str] = None

class TechProposal(BaseModel):
    executive_summary: str
    system_architecture: SystemArchitecture
    tech_stack: TechStack
    database_schema: DatabaseSchema
    api_design: APIDesign
    deployment_strategy: DeploymentStrategy
    security_measures: List[str]
    scalability_plan: str
    performance_considerations: Optional[str] = None
    cost_optimization: Optional[str] = None

class TechProposalAgent:
    def __init__(self):
        self.llm_service = LLMService()
    
    async def generate_proposal(
        self,
        rfp_data: RFPExtraction,
        similar_projects: List[PastProjectData],
        knowledge_highlights: List[KnowledgeHighlight] = []
    ) -> TechProposal:
        """Generate comprehensive technical proposal"""
        
        logger.info(f"Generating proposal for: {rfp_data.project_title}")
        
        # Prepare context from similar projects and knowledge highlights
        projects_context = self._format_projects_context(similar_projects)
        highlights_context = self._format_highlights_context(knowledge_highlights)
        requirements_context = self._format_requirements_context(rfp_data)
        
        # Generate proposal using LLM
        prompt = PROMPT_TEMPLATES["GENERATE_ARCHITECTURE"](
            requirements_context,
            projects_context,
            highlights_context
        )
        
        response = await self.llm_service.call_llm_json(
            system_prompt=SYSTEM_PROMPTS["TECH_ARCHITECT"],
            user_prompt=prompt,
            response_schema=TechProposal.model_json_schema()
        )
        
        # Parse and validate
        proposal = TechProposal(**response)
        
        logger.info("Proposal generation completed successfully")
        return proposal
    
    def _format_requirements_context(self, rfp: RFPExtraction) -> str:
        """Format RFP requirements as context"""
        return f"""
Project: {rfp.project_title}
Timeline: {rfp.timeline.get('min_weeks')}-{rfp.timeline.get('max_weeks')} weeks
Budget: ${rfp.budget.get('min', 0)}-${rfp.budget.get('max', 0)}

Must-Have Features:
{json.dumps(rfp.must_have_features, indent=2)}

Nice-to-Have Features:
{json.dumps(rfp.nice_to_have_features, indent=2)}

Technical Requirements:
{json.dumps([r.dict() for r in rfp.tech_requirements], indent=2)}

Constraints:
{json.dumps(rfp.constraints, indent=2)}

Compliance Requirements:
{json.dumps(rfp.compliance_requirements, indent=2)}
        """.strip()
    
    def _format_projects_context(self, projects: List[PastProjectData]) -> str:
        """Format similar projects as context"""
        if not projects:
            return "No similar past projects found."
        
        projects_text = "Similar Past Projects:\n\n"
        for p in projects:
            projects_text += f"""
Project: {p.name}
Tech Stack: {', '.join(p.tech_stack)}
Timeline: {p.timeline_actual} weeks (estimated: {p.timeline_estimated})
Cost: ${p.cost_actual:,.0f} (estimated: ${p.cost_estimated:,.0f})
Team Size: {p.team_size}
Lessons Learned: {p.lessons_learned}
Challenges: {', '.join(p.challenges)}
---
            """
        
        return projects_text

    def _format_highlights_context(self, highlights: List[KnowledgeHighlight]) -> str:
        """Format knowledge highlights for LLM context"""
        if not highlights:
            return ""
            
        context = "Relevant Company Knowledge Highlights:\n\n"
        for h in highlights:
            context += f"- Source: {h.source_file}\n  Content: {h.content}\n\n"
        return context
    
    def generate_architecture_diagram(self, proposal: TechProposal) -> str:
        """Generate ASCII architecture diagram"""
        return f"""
    ┌─────────────────────────────────────────┐
    │         Frontend Layer                  │
    │  ({', '.join(proposal.tech_stack.frontend[:2])})
    └──────────────┬──────────────────────────┘
                   │
    ┌──────────────▼──────────────────────────┐
    │      API Gateway / Load Balancer        │
    │      ({', '.join(proposal.tech_stack.devops[:1])})
    └──────────────┬──────────────────────────┘
                   │
    ┌──────────────▼──────────────────────────┐
    │      Backend Services                   │
    │  ({', '.join(proposal.tech_stack.backend[:2])})
    └──────────────┬──────────────────────────┘
                   │
    ┌──────────────┴──────────────────────────┐
    │                                         │
┌───▼────────────────────┐         ┌─────────▼──────┐
│   Database             │         │   Cache        │
│ ({proposal.tech_stack.database[0]})        │     (Redis)    │
└────────────────────────┘         └────────────────┘

External Integrations:
{', '.join(proposal.api_design.endpoints[0].path for _ in range(1)) if proposal.api_design.endpoints else 'N/A'}

Monitoring & Logging:
{', '.join(proposal.deployment_strategy.monitoring)}
        """.strip()