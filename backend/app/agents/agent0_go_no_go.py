# backend/app/agents/agent0_go_no_go.py

import logging
from typing import Dict, List, Any
from pydantic import BaseModel, Field
from backend.app.services.llm_service import LLMService
from backend.app.utils.prompts import SYSTEM_PROMPTS, PROMPT_TEMPLATES
from backend.app.agents.agent1_rfp_parser import RFPExtraction
import json

logger = logging.getLogger(__name__)

class GoNoGoDecision(BaseModel):
    decision: str = Field(..., description="'Go' or 'No-Go'")
    reasoning: str = Field(..., description="Explanation for the decision")
    risk_level: str = Field(..., description="'Low', 'Medium', 'High', or 'Critical'")
    red_flags: List[str] = Field(default_factory=list, description="List of major issues")

class GoNoGoAgent:
    def __init__(self):
        self.llm_service = LLMService()
        
    async def evaluate_rfp(self, rfp_extraction: RFPExtraction) -> GoNoGoDecision:
        """Evaluate the parsed RFP to make a Go/No-Go decision"""
        logger.info(f"Starting Go/No-Go evaluation for project: {rfp_extraction.project_title}")
        
        # Serialize the extraction data to pass to the LLM
        rfp_json = json.dumps(rfp_extraction.model_dump(), default=str)
        prompt = PROMPT_TEMPLATES["EVALUATE_GO_NO_GO"](rfp_json)
        
        try:
            response = await self.llm_service.call_llm_json(
                system_prompt=SYSTEM_PROMPTS["GO_NO_GO_EVALUATOR"],
                user_prompt=prompt,
                response_schema=GoNoGoDecision.model_json_schema()
            )
            
            # Parse and validate
            decision = GoNoGoDecision(**response)
            logger.info(f"Go/No-Go Decision: {decision.decision} with risk level {decision.risk_level}")
            return decision
            
        except Exception as e:
            logger.error(f"Go/No-Go evaluation failed: {e}")
            # Fallback to Go if the AI fails, so we don't break the pipeline
            return GoNoGoDecision(
                decision="Go",
                reasoning=f"Automatic 'Go' fallback due to evaluation error: {str(e)}",
                risk_level="Unknown",
                red_flags=[]
            )
