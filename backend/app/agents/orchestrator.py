# backend/app/agents/orchestrator.py
import logging
import json
from typing import AsyncGenerator, Dict, Any
from backend.app.agents.agent0_go_no_go import GoNoGoAgent, GoNoGoDecision
from backend.app.agents.agent1_rfp_parser import RFPParserAgent, RFPExtraction
from backend.app.agents.agent2_rag_search import RAGSearchAgent
from backend.app.agents.agent3_tech_proposal import TechProposalAgent
from backend.app.agents.agent4_estimation import EstimationAgent
from backend.app.agents.agent5_legal_compliance import LegalComplianceAgent
from backend.app.agents.agent6_team_allocation import TeamAllocationAgent
from backend.app.services.db_service import DatabaseService
from backend.app.models.bid import Bid
from uuid import uuid4

logger = logging.getLogger(__name__)

class BidOrchestrator:
    def __init__(self):
        self.go_no_go = GoNoGoAgent()
        self.parser = RFPParserAgent()
        self.rag = RAGSearchAgent()
        self.tech = TechProposalAgent()
        self.estimator = EstimationAgent()
        self.legal = LegalComplianceAgent()
        self.team_maker = TeamAllocationAgent()
        self.db = DatabaseService()
        
    async def start_bid_streaming(
        self, file_path: str, company_id: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        
        yield {"status": "starting", "stage": "starting", "message": "Initializing AI agents", "progress": 5}
        
        try:
            # Step 1: Parse RFP
            yield {"status": "parsing", "stage": "parsing", "message": "Parsing RFP document...", "progress": 10}
            rfp_extraction = await self.parser.parse_rfp(file_path)
            yield {"status": "parsing_complete", "stage": "parsing_complete", "data": rfp_extraction.model_dump(), "progress": 25}
            
            # Step 1.5: Go/No-Go Evaluation
            yield {"status": "evaluating", "stage": "evaluating", "message": "Evaluating bid feasibility (Go/No-Go)...", "progress": 27}
            go_no_go_decision = await self.go_no_go.evaluate_rfp(rfp_extraction)
            
            # Save early to allow continuing later
            new_bid = Bid(
                company_id=str(company_id),
                rfp_file_path=file_path,
                rfp_extraction=rfp_extraction.model_dump(),
                go_no_go_decision=go_no_go_decision.model_dump(),
                status="draft"
            )
            if new_bid.id is None:
                new_bid.id = uuid4()
            saved_bid = await self.db.save_bid(new_bid)
            
            if go_no_go_decision.decision == "No-Go":
                saved_bid.status = "requires_confirmation"
                await self.db.save_bid(saved_bid)
                yield {"status": "requires_confirmation", "stage": "evaluation_complete", "message": "Project flagged as No-Go.", "data": go_no_go_decision.model_dump(), "bid_id": str(saved_bid.id), "progress": 30}
                return # Halt!

            yield {"status": "evaluation_complete", "stage": "evaluation_complete", "message": "Decision: Go", "data": go_no_go_decision.model_dump(), "progress": 29}
            
            # Yield from phase 2 automatically if GO
            async for chunk in self.continue_bid_streaming(str(saved_bid.id), str(company_id)):
                yield chunk
                
        except Exception as e:
            logger.error(f"Orchestration Phase 1 failed: {str(e)}")
            yield {"status": "error", "message": str(e)}

    async def continue_bid_streaming(
        self, bid_id: str, company_id: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        
        try:
            saved_bid = await self.db.get_bid_by_id(bid_id)
            if not saved_bid:
                yield {"status": "error", "message": "Bid not found"}
                return
                
            rfp_extraction = RFPExtraction(**saved_bid.rfp_extraction)
            go_no_go_decision = GoNoGoDecision(**saved_bid.go_no_go_decision)
            
            # Step 2: RAG Search for historical context
            yield {"status": "searching", "stage": "searching", "message": "Finding similar past projects and company knowledge...", "progress": 30}
            rfp_summary = json.dumps(rfp_extraction.model_dump())
            search_results = await self.rag.find_similar_projects(rfp_summary, str(company_id))
            similar_projects = search_results["projects"]
            knowledge_highlights = search_results["knowledge_highlights"]
            historical_data = self.rag.extract_insights(similar_projects)
            yield {"status": "search_complete", "stage": "search_complete", "message": f"Found {len(similar_projects)} projects and {len(knowledge_highlights)} knowledge highlights", "progress": 45}
            
            # Step 3: Technical Proposal
            yield {"status": "designing", "stage": "designing", "message": "Drafting technical architecture with company insights...", "progress": 50}
            tech_proposal = await self.tech.generate_proposal(rfp_extraction, similar_projects, knowledge_highlights)
            yield {"status": "design_complete", "stage": "design_complete", "data": tech_proposal.model_dump(), "progress": 70}
            
            # Step 4: Estimation
            yield {"status": "estimating", "stage": "estimating", "message": "Calculating time and cost estimates...", "progress": 70}
            estimation = await self.estimator.generate_estimate(
                rfp_extraction, tech_proposal, historical_data, similar_projects, knowledge_highlights
            )
            yield {"status": "estimation_complete", "stage": "estimation_complete", "data": estimation.model_dump(), "progress": 80}
            
            # Step 4.5: Staffing / Resource Allocation
            yield {"status": "staffing", "stage": "staffing", "message": "Matching team roles with company CVs...", "progress": 82}
            team_allocation = await self.team_maker.allocate_team(
                [t.model_dump() for t in estimation.team_composition], 
                company_id
            )
            yield {"status": "staffing_complete", "stage": "staffing_complete", "data": team_allocation.model_dump(), "progress": 87}
            
            # Step 5: Legal Compliance
            yield {"status": "legal_check", "stage": "legal_check", "message": "Analyzing legal and compliance risks...", "progress": 90}
            legal_analysis = await self.legal.check_compliance(rfp_extraction, tech_proposal)
            yield {"status": "legal_complete", "stage": "legal_complete", "data": legal_analysis.model_dump(), "progress": 95}
            
            # Save final results
            yield {"status": "saving", "stage": "saving", "message": "Saving proposal to database...", "progress": 95}
            
            saved_bid.technical_proposal = tech_proposal.model_dump()
            saved_bid.estimation = estimation.model_dump()
            saved_bid.allocated_team = team_allocation.model_dump()
            saved_bid.legal_compliance = legal_analysis.model_dump()
            saved_bid.status = "draft"
            saved_bid.bid_amount = estimation.final_estimate.total_cost
            saved_bid.bid_timeline_weeks = estimation.final_estimate.timeline_weeks
            
            await self.db.save_bid(saved_bid)
            
            # Flatten data for frontend bid.html expectations
            final_data = saved_bid.to_dict()
            final_data.update(rfp_extraction.model_dump())
            final_data.update({
                "go_no_go": go_no_go_decision.decision,
                "go_no_go_reason": go_no_go_decision.reasoning,
                " executive_summary": tech_proposal.executive_summary,
                "tech_stack": tech_proposal.tech_stack.model_dump(),
                "allocated_team": team_allocation.model_dump(),
                "legal_summary": legal_analysis.overall_summary,
                "total_cost_usd": estimation.final_estimate.total_cost,
                "timeline_weeks": estimation.final_estimate.timeline_weeks
            })

            yield {
                "status": "complete", 
                "stage": "complete",
                "message": "Bid generation successful",
                "progress": 100,
                "data": final_data,
                "bid_id": str(saved_bid.id)
            }
            
        except Exception as e:
            logger.error(f"Orchestration Phase 2 failed: {str(e)}")
            yield {"status": "error", "message": str(e)}
