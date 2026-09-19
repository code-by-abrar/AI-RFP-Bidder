# backend/app/services/export_service.py

import os
import json
from datetime import datetime
from uuid import uuid4
try:
    from docx import Document
    from docx.shared import Pt, Inches
except ImportError:
    # Fallback if python-docx is not installed
    pass

class DocumentExportService:
    
    @staticmethod
    def generate_word_document(bid_data: dict) -> str:
        """
        Generates a Word document from the bid data.
        Returns the path to the generated file.
        """
        doc = Document()
        
        # Extract Data
        rfp = bid_data.get("rfp_extraction", {}) or {}
        go_no_go = bid_data.get("go_no_go_decision", {}) or {}
        tech = bid_data.get("technical_proposal", {}) or {}
        est = bid_data.get("estimation", {}) or {}
        legal = bid_data.get("legal_compliance", {}) or {}
        
        # --- Title ---
        title = rfp.get("project_title", "Software Development Proposal")
        doc.add_heading(title, 0)
        
        client_name = rfp.get("client_name", "Valued Client")
        doc.add_paragraph(f"Prepared for: {client_name}")
        doc.add_paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}")
        
        doc.add_page_break()
        
        # --- Internal Go/No-Go Decision (Optional, usually for internal review but we'll include it per requirement) ---
        if go_no_go:
            doc.add_heading("Internal Evaluation (Go/No-Go)", level=1)
            decision = go_no_go.get("decision", "Unknown")
            p = doc.add_paragraph(f"Decision: ")
            p.add_run(decision).bold = True
            doc.add_paragraph(f"Reasoning: {go_no_go.get('reasoning', '')}")
            doc.add_paragraph(f"Risk Level: {go_no_go.get('risk_level', '')}")
            
        # --- Executive Summary ---
        doc.add_heading("Executive Summary", level=1)
        doc.add_paragraph(tech.get("executive_summary", "This proposal outlines our approach to delivering a high-quality solution tailored to your requirements."))
        
        # --- Architecture & Tech Stack ---
        doc.add_heading("Technical Architecture", level=1)
        arch = tech.get("system_architecture", "")
        if arch:
            doc.add_paragraph(arch)
            
        doc.add_heading("Proposed Technologies", level=2)
        stack = tech.get("tech_stack", {})
        if stack:
            # Depending on how the dict is structured, we print keys and values
            if isinstance(stack, dict):
                for k, v in stack.items():
                    if v:
                        doc.add_paragraph(f"{str(k).title()}: {v}", style='List Bullet')
            elif isinstance(stack, list):
                for item in stack:
                    doc.add_paragraph(str(item), style='List Bullet')
        
        # --- Estimation & Timeline ---
        doc.add_heading("Estimation & Timeline", level=1)
        
        final_est = est.get("final_estimate", {})
        if final_est:
            cost = final_est.get("total_cost", "TBD")
            weeks = final_est.get("timeline_weeks", "TBD")
            
            p = doc.add_paragraph("Total Estimated Cost: ")
            p.add_run(f"${cost} USD").bold = True
            
            p = doc.add_paragraph("Estimated Timeline: ")
            p.add_run(f"{weeks} Weeks").bold = True
            
        doc.add_heading("Phase Breakdown", level=2)
        phases = est.get("phases", [])
        for phase in phases:
            if isinstance(phase, dict):
                p_name = phase.get("name", "Phase")
                p_weeks = phase.get("duration_weeks", "")
                p_cost = phase.get("cost", "")
                doc.add_paragraph(f"{p_name} ({p_weeks} weeks) - ${p_cost}", style='List Bullet')
                
        # --- Proposed Team ---
        allocated_team = bid_data.get("allocated_team", {})
        if allocated_team and "allocated_team" in allocated_team:
            doc.add_heading("Proposed Project Team", level=1)
            for member in allocated_team["allocated_team"]:
                p = doc.add_paragraph()
                p.add_run(f"{member.get('assigned_name', 'TBD')}").bold = True
                p.add_run(f" - {member.get('role', 'Resource')}\n").italic = True
                p.add_run(f"{member.get('reasoning', '')}")

        # --- Legal & Compliance ---
        doc.add_heading("Compliance & Assumptions", level=1)
        legal_sum = legal.get("overall_summary", "")
        if legal_sum:
            doc.add_paragraph(legal_sum)
            
        assumptions = est.get("assumptions", [])
        if assumptions:
            doc.add_heading("Key Assumptions", level=2)
            for a in assumptions:
                doc.add_paragraph(str(a), style='List Bullet')
                
        # Save Document
        os.makedirs(".data/exports", exist_ok=True)
        filename = f".data/exports/proposal_{uuid4().hex[:8]}.docx"
        doc.save(filename)
        
        return filename
