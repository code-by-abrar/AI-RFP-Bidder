# backend/app/agents/agent4_estimation.py

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np
from pydantic import BaseModel, Field
from backend.app.agents.agent1_rfp_parser import RFPExtraction
from backend.app.agents.agent3_tech_proposal import TechProposal
from backend.app.agents.agent2_rag_search import HistoricalInsights, PastProjectData, KnowledgeHighlight
from backend.app.services.llm_service import LLMService
from backend.app.utils.prompts import SYSTEM_PROMPTS, PROMPT_TEMPLATES

logger = logging.getLogger(__name__)

class Phase(BaseModel):
    name: str
    duration_weeks: int
    description: str
    deliverables: List[str]
    dependencies: Optional[List[str]] = None

class Timeline(BaseModel):
    phases: List[Phase]
    total_duration_weeks: int
    confidence_level: str = Field(default="medium", description="low, medium, high")
    assumptions: List[str]
    critical_path: Optional[str] = None

class CostBreakdown(BaseModel):
    category: str
    hours: float
    rate_per_hour: float
    total: float

class Cost(BaseModel):
    breakdown: List[CostBreakdown]
    total_cost: float
    currency: str = "USD"
    margin_applied: float = 0.15
    contingency_percentage: float = 0.20

class TeamMember(BaseModel):
    role: str
    count: int
    seniority: str
    monthly_cost: float
    allocation_percentage: float = 100.0

class RiskFactor(BaseModel):
    risk: str
    impact: str = Field(description="low, medium, high")
    buffer_percentage: float
    mitigation_strategy: Optional[str] = None

class FinalEstimate(BaseModel):
    total_hours: float
    total_cost: float
    timeline_weeks: int
    buffer_included: float
    risk_adjusted_cost: float

class Estimation(BaseModel):
    timeline: Timeline
    cost: Cost
    team_composition: List[TeamMember]
    risk_factors: List[RiskFactor]
    final_estimate: FinalEstimate
    notes: Optional[str] = None

class EstimationAgent:
    def __init__(self):
        self.llm_service = LLMService()
    
    async def generate_estimate(
        self,
        rfp_data: RFPExtraction,
        proposal: TechProposal,
        historical_data: HistoricalInsights,
        similar_projects: List[PastProjectData],
        knowledge_highlights: List[KnowledgeHighlight] = []
    ) -> Estimation:
        """Generate comprehensive estimation"""
        
        logger.info(f"Generating estimation for: {rfp_data.project_title}")
        
        # Step 1: Calculate base estimation
        base_estimate = self._calculate_base_estimate(rfp_data, proposal)
        
        # Step 2: Adjust for historical data
        adjusted_estimate = self._adjust_for_history(
            base_estimate, 
            historical_data, 
            similar_projects
        )
        
        # Step 3: Add buffer and contingency
        final_estimate = self._add_buffer_and_contingency(adjusted_estimate)
        
        # Step 4: Break into phases
        phased_estimate = self._break_into_phases(final_estimate)
        
        # Step 5: Refine with LLM (AI Insight)
        refined_estimate = await self._refine_with_llm(
            phased_estimate,
            rfp_data,
            proposal,
            historical_data,
            knowledge_highlights
        )
        
        logger.info(
            f"Estimation: {refined_estimate.final_estimate.total_cost:,.0f} USD, "
            f"{refined_estimate.final_estimate.timeline_weeks} weeks"
        )
        
        return refined_estimate

    async def _refine_with_llm(
        self,
        estimate: Estimation,
        rfp: RFPExtraction,
        proposal: TechProposal,
        history: HistoricalInsights,
        highlights: List[KnowledgeHighlight] = []
    ) -> Estimation:
        """Use LLM to refine the rule-based estimation with expert insights"""
        
        # Prepare context
        req_context = f"Project: {rfp.project_title}\nFeatures: {rfp.must_have_features}"
        arch_context = f"Tech: {proposal.tech_stack.model_dump()}\nArch: {proposal.system_architecture.description}"
        history_context = f"Avg Timeline: {history.average_timeline} weeks\nChallenges: {history.common_challenges}"
        h_context = "\n".join([f"- {h.content}" for h in highlights])
        
        prompt = PROMPT_TEMPLATES["ESTIMATE_PROJECT"](
            req_context,
            arch_context,
            history_context,
            h_context
        )
        
        try:
            # We call LLM to get a JSON update for the estimate
            response = await self.llm_service.call_llm_json(
                system_prompt=SYSTEM_PROMPTS["ESTIMATOR"],
                user_prompt=prompt,
                response_schema=Estimation.model_json_schema()
            )
            
            # Merge LLM insights with our rule-based math
            # We trust LLM for risks and notes, but keep our math as a baseline
            llm_estimate = Estimation(**response)
            
            # Update notes and risks from AI
            estimate.notes = llm_estimate.notes
            estimate.risk_factors = llm_estimate.risk_factors
            
            # If AI is significantly higher in cost/time, we adjust
            if llm_estimate.final_estimate.total_cost > estimate.final_estimate.total_cost:
                estimate.final_estimate.total_cost = llm_estimate.final_estimate.total_cost
                
            if llm_estimate.final_estimate.timeline_weeks > estimate.final_estimate.timeline_weeks:
                estimate.final_estimate.timeline_weeks = llm_estimate.final_estimate.timeline_weeks
                
            return estimate
            
        except Exception as e:
            logger.error(f"LLM refinement failed, falling back to rule-based: {e}")
            return estimate
    
    def _calculate_base_estimate(
        self,
        rfp: RFPExtraction,
        proposal: TechProposal
    ) -> Estimation:
        """Calculate base estimation using component method"""
        
        # Estimate each component
        frontend_estimate = self._estimate_frontend(rfp)
        backend_estimate = self._estimate_backend(rfp, proposal)
        database_estimate = self._estimate_database(proposal)
        testing_estimate = self._estimate_testing(
            frontend_estimate + backend_estimate
        )
        deployment_estimate = self._estimate_deployment(proposal)
        documentation_estimate = self._estimate_documentation(rfp)
        
        # Total hours
        total_hours = (
            frontend_estimate +
            backend_estimate +
            database_estimate +
            testing_estimate +
            deployment_estimate +
            documentation_estimate
        )
        
        # Create breakdown
        breakdown = [
            CostBreakdown(category="Frontend", hours=frontend_estimate, rate_per_hour=75, total=0),
            CostBreakdown(category="Backend", hours=backend_estimate, rate_per_hour=100, total=0),
            CostBreakdown(category="Database", hours=database_estimate, rate_per_hour=85, total=0),
            CostBreakdown(category="Testing", hours=testing_estimate, rate_per_hour=70, total=0),
            CostBreakdown(category="Deployment", hours=deployment_estimate, rate_per_hour=100, total=0),
            CostBreakdown(category="Documentation", hours=documentation_estimate, rate_per_hour=60, total=0),
        ]
        
        # Calculate totals
        for item in breakdown:
            item.total = item.hours * item.rate_per_hour
        
        total_cost = sum(item.total for item in breakdown)
        
        return Estimation(
            timeline=Timeline(
                phases=[],
                total_duration_weeks=int(np.ceil(total_hours / 40)),
                assumptions=self._get_assumptions(rfp)
            ),
            cost=Cost(breakdown=breakdown, total_cost=total_cost),
            team_composition=self._get_team_composition(total_hours),
            risk_factors=self._identify_risks(rfp),
            final_estimate=FinalEstimate(
                total_hours=total_hours,
                total_cost=total_cost,
                timeline_weeks=int(np.ceil(total_hours / 40)),
                buffer_included=0,
                risk_adjusted_cost=0
            )
        )
    
    def _estimate_frontend(self, rfp: RFPExtraction) -> float:
        """Estimate frontend development hours"""
        feature_count = len(rfp.must_have_features)
        base_hours = 20  # Per feature
        
        # Complexity multiplier
        complexity = 1.0
        if any("real-time" in f.lower() for f in rfp.must_have_features):
            complexity *= 1.3
        if any("mobile" in f.lower() for f in rfp.must_have_features):
            complexity *= 1.5
        
        return feature_count * base_hours * complexity
    
    def _estimate_backend(self, rfp: RFPExtraction, proposal: TechProposal) -> float:
        """Estimate backend development hours"""
        api_endpoints = len(proposal.api_design.endpoints)
        base_hours = api_endpoints * 15  # 15 hours per endpoint
        
        # Complexity multiplier
        complexity = 1.0
        if len(rfp.constraints) > 3:
            complexity *= 1.2
        if any("real-time" in c.lower() for c in rfp.constraints):
            complexity *= 1.5
        
        return base_hours * complexity
    
    def _estimate_database(self, proposal: TechProposal) -> float:
        """Estimate database design and implementation"""
        table_count = len(proposal.database_schema.tables)
        return max(table_count * 10, 40)  # Minimum 40 hours
    
    def _estimate_testing(self, dev_hours: float) -> float:
        """Testing = 30% of dev hours"""
        return dev_hours * 0.3
    
    def _estimate_deployment(self, proposal: TechProposal) -> float:
        """Estimate deployment and infrastructure setup"""
        return 40  # Standard deployment hours
    
    def _estimate_documentation(self, rfp: RFPExtraction) -> float:
        """Estimate documentation hours"""
        return 30  # Standard documentation
    
    def _adjust_for_history(
        self,
        estimate: Estimation,
        historical_data: HistoricalInsights,
        similar_projects: List[PastProjectData]
    ) -> Estimation:
        """Adjust estimate based on historical data"""
        
        if not similar_projects:
            return estimate
        
        # Calculate adjustment factor
        estimated_weeks = estimate.final_estimate.timeline_weeks
        if historical_data.average_timeline > 0:
            adjustment_factor = historical_data.average_timeline / estimated_weeks
            
            # Apply adjustment (but cap at 1.5x)
            adjustment_factor = min(adjustment_factor, 1.5)
            
            # Adjust timeline
            estimate.final_estimate.timeline_weeks = int(
                estimate.final_estimate.timeline_weeks * adjustment_factor
            )
            estimate.timeline.total_duration_weeks = estimate.final_estimate.timeline_weeks
        
        return estimate
    
    def _add_buffer_and_contingency(self, estimate: Estimation) -> Estimation:
        """Add safety buffer and contingency"""
        
        # Base contingency = 20%
        contingency_hours = estimate.final_estimate.total_hours * 0.2
        
        # Additional buffer for risks
        total_risk_buffer = sum(
            (rf.buffer_percentage / 100.0 * estimate.final_estimate.total_hours)
            for rf in estimate.risk_factors
        )
        
        # Total buffer
        total_buffer_hours = contingency_hours + total_risk_buffer
        
        # Update estimate
        estimate.final_estimate.total_hours += total_buffer_hours
        estimate.final_estimate.buffer_included = total_buffer_hours
        
        # Recalculate costs
        total_cost = 0
        for item in estimate.cost.breakdown:
            item.total = item.hours * item.rate_per_hour
            total_cost += item.total
        
        # Add margin
        margin = total_cost * estimate.cost.margin_applied
        estimate.cost.total_cost = total_cost + margin
        estimate.final_estimate.total_cost = total_cost + margin
        
        # Risk-adjusted cost (cost + 10% risk buffer)
        estimate.final_estimate.risk_adjusted_cost = (
            estimate.final_estimate.total_cost * 1.1
        )
        
        return estimate
    
    def _break_into_phases(self, estimate: Estimation) -> Estimation:
        """Break project into phases"""
        
        total_weeks = estimate.final_estimate.timeline_weeks
        
        estimate.timeline.phases = [
            Phase(
                name="Discovery & Planning",
                duration_weeks=2,
                description="Requirements finalization, architecture design review",
                deliverables=["Final Requirements Doc", "Architecture Diagram", "Tech Design Review"]
            ),
            Phase(
                name="Development",
                duration_weeks=max(total_weeks - 5, 4),
                description="Frontend, Backend, Database implementation",
                deliverables=["Feature Code", "API Documentation", "Database Schema"]
            ),
            Phase(
                name="Testing & QA",
                duration_weeks=2,
                description="Unit, integration, and E2E testing",
                deliverables=["Test Report", "Bug Fixes", "Test Coverage Report"]
            ),
            Phase(
                name="Deployment & Training",
                duration_weeks=1,
                description="Production deployment and client training",
                deliverables=["Live System", "Training Materials", "Deployment Guide"]
            ),
        ]
        
        return estimate
    
    def _get_team_composition(self, total_hours: float) -> List[TeamMember]:
        """Determine team composition"""
        
        # Calculate team size (roughly 1 person per 200 hours)
        team_size = max(int(total_hours / 200), 2)
        
        return [
            TeamMember(
                role="Project Manager",
                count=1,
                seniority="senior",
                monthly_cost=50000
            ),
            TeamMember(
                role="Senior Developer",
                count=max(1, team_size // 2),
                seniority="senior",
                monthly_cost=45000
            ),
            TeamMember(
                role="Junior Developer",
                count=max(1, team_size // 3),
                seniority="junior",
                monthly_cost=20000
            ),
            TeamMember(
                role="QA Engineer",
                count=1,
                seniority="senior",
                monthly_cost=30000
            ),
        ]
    
    def _identify_risks(self, rfp: RFPExtraction) -> List[RiskFactor]:
        """Identify project risks"""
        
        risks = []
        
        # Technology risks
        if any("AI" in t.technology or "ML" in t.technology for t in rfp.tech_requirements):
            risks.append(RiskFactor(
                risk="ML Model Integration Complexity",
                impact="high",
                buffer_percentage=30,
                mitigation_strategy="Allocate senior ML engineer early"
            ))
        
        # Scalability risks
        if any("scalable" in c.lower() or "large scale" in c.lower() for c in rfp.constraints):
            risks.append(RiskFactor(
                risk="Scalability Architecture Complexity",
                impact="high",
                buffer_percentage=25
            ))
        
        # Timeline risks
        max_weeks = rfp.timeline.get('max_weeks') or 0
        if max_weeks < 8 and max_weeks > 0:
            risks.append(RiskFactor(
                risk="Aggressive Timeline",
                impact="high",
                buffer_percentage=20,
                mitigation_strategy="Parallel track development, reduce scope"
            ))
        
        # Integration risks
        if len(rfp.integrations) > 3:
            risks.append(RiskFactor(
                risk="Multiple Third-party Integrations",
                impact="medium",
                buffer_percentage=15
            ))
        
        # Security/Compliance risks
        if len(rfp.compliance_requirements) > 0:
            risks.append(RiskFactor(
                risk="Compliance Requirements",
                impact="medium",
                buffer_percentage=10,
                mitigation_strategy="Security audit, compliance review"
            ))
        
        return risks
    
    def _get_assumptions(self, rfp: RFPExtraction) -> List[str]:
        """Generate estimation assumptions"""
        return [
            "Client will provide clear requirements and timely feedback",
            "No major scope changes after project kickoff",
            "Standard technology stack with no cutting-edge unproven tech",
            "Development team has experience with required technologies",
            "Infrastructure provisioning handled by client or ops team",
            "Team has minimum 40 hours/week availability",
            "APIs from third-party services are well-documented and stable",
            "Client will not request major design changes during development",
        ]