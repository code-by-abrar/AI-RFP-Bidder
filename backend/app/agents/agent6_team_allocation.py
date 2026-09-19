# backend/app/agents/agent6_team_allocation.py

import logging
from typing import List, Optional
from pydantic import BaseModel
from backend.app.services.llm_service import LLMService
from backend.app.services.db_service import SessionLocal
from backend.app.models.employee import Employee
from backend.app.utils.prompts import SYSTEM_PROMPTS, PROMPT_TEMPLATES

logger = logging.getLogger(__name__)

class AllocatedResource(BaseModel):
    assigned_name: str
    role: str
    reasoning: str

class AllocatedTeam(BaseModel):
    allocated_team: List[AllocatedResource]

class TeamAllocationAgent:
    def __init__(self):
        self.llm_service = LLMService()

    async def allocate_team(self, team_composition: list, company_id: str) -> AllocatedTeam:
        """Matches Estimation team requirements with DB Employees"""
        logger.info(f"Allocating team for company {company_id}")
        
        # 1. Fetch available employees natively
        available_employees = []
        if SessionLocal:
            def _get_bench():
                with SessionLocal() as db:
                    return db.query(Employee).filter(
                        Employee.company_id == company_id,
                        Employee.is_available == True
                    ).all()
            
            import asyncio
            db_employees = await asyncio.to_thread(_get_bench)
            
            for emp in db_employees:
                available_employees.append({
                    "id": str(emp.id),
                    "name": emp.name,
                    "role": emp.role,
                    "seniority": emp.seniority,
                    "skills": emp.skills
                })
        
        if not available_employees:
            logger.warning("No employees available on bench.")
        
        # 2. Format required roles from dicts
        req_str = "\n".join([f"- {r['count']}x {r['seniority'].title()} {r['role']}" for r in team_composition])
        bench_str = "\n".join([f"- {e['name']} ({e['seniority'].title()} {e['role']}): {', '.join(e['skills'] or [])}" for e in available_employees])
        
        if not bench_str:
            bench_str = "None available."

        prompt = PROMPT_TEMPLATES["TEAM_ALLOCATION"](req_str, bench_str)
        
        try:
            response = await self.llm_service.call_llm_json(
                system_prompt=SYSTEM_PROMPTS["TEAM_MAKER"],
                user_prompt=prompt,
                response_schema=AllocatedTeam.model_json_schema()
            )
            return AllocatedTeam(**response)
        except Exception as e:
            logger.error(f"Team Allocation LLM failed: {e}")
            # Fallback
            fallback = []
            for role in team_composition:
                for _ in range(role.get("count", 1)):
                    fallback.append(AllocatedResource(
                        assigned_name="Hiring Required",
                        role=role.get("role", "Engineer"),
                        reasoning="AI matching failed. Fallback to manual hiring allocation."
                    ))
            return AllocatedTeam(allocated_team=fallback)
