# backend/app/agents/agent7_questionnaire_filler.py

import os
import pandas as pd
import logging
from uuid import uuid4
from typing import Optional
from backend.app.services.llm_service import LLMService
from backend.app.agents.agent2_rag_search import RAGSearchAgent
from backend.app.utils.prompts import SYSTEM_PROMPTS, PROMPT_TEMPLATES

logger = logging.getLogger(__name__)

class QuestionnaireFillerAgent:
    def __init__(self):
        self.llm_service = LLMService()
        self.rag_agent = RAGSearchAgent()
        
        # Possible variations of column headers that hold the questions
        self.question_keywords = ['question', 'requirement', 'control', 'description', 'query', 'criteria']
        
    async def process_excel_questionnaire(self, file_path: str, company_id: str) -> str:
        """
        Reads an Excel file, queries RAG, fills answers, and saves it.
        Returns the path to the newly saved populated Excel file.
        """
        logger.info(f"Loading Excel questionnaire: {file_path}")
        
        try:
            # Read all sheets, we will process the first sheet by default for simplicity
            xl = pd.ExcelFile(file_path)
            sheet_name = xl.sheet_names[0]  # Just grabbing the first visible sheet
            df = pd.read_excel(xl, sheet_name=sheet_name)
            
            # Step 1: Detect the Question column
            q_col = self._detect_question_column(df)
            if not q_col:
                raise ValueError("Could not auto-detect a 'Question' column in the Excel file. Please ensure a column header contains the word 'Question' or 'Requirement'.")
                
            # Step 2: Ensure an Answer column exists
            a_col = "AI_Generated_Answer"
            if "Answer" in df.columns:
                a_col = "Answer"
            elif "Response" in df.columns:
                a_col = "Response"
            elif "Vendor Response" in df.columns:
                a_col = "Vendor Response"
            else:
                df["AI_Generated_Answer"] = ""
                
            # Step 3: Iterate and fill
            for idx, row in df.iterrows():
                question = str(row[q_col]).strip()
                
                # Skip empty questions
                if pd.isna(question) or question.lower() == 'nan' or len(question) < 5:
                    continue
                    
                # RAG Lookup
                context = await self.rag_agent.query_knowledge_base(question, str(company_id))
                
                # LLM Call
                prompt = PROMPT_TEMPLATES["QUESTIONNAIRE_FILLER"](question, context)
                try:
                    # We use standard call_llm because we just want the pure text answer for Excel
                    answer = await self.llm_service.call_llm(
                        system_prompt=SYSTEM_PROMPTS["COMPLIANCE_FILLER"],
                        user_prompt=prompt
                    )
                    
                    df.at[idx, a_col] = answer.strip()
                    logger.info(f"Filled row {idx} / {len(df)}")
                except Exception as e:
                    logger.error(f"Failed to generate answer for row {idx}: {e}")
                    df.at[idx, a_col] = "Error generating response."
                    
            # Save logic
            os.makedirs(".data/exports", exist_ok=True)
            new_filename = f".data/exports/filled_questionnaire_{uuid4().hex[:8]}.xlsx"
            
            # Use openpyxl engine to save Excel 
            df.to_excel(new_filename, index=False, sheet_name=sheet_name)
            logger.info(f"Populated questionnaire saved to: {new_filename}")
            
            return new_filename
            
        except Exception as e:
            logger.error(f"Excel processing failed: {str(e)}")
            raise

    def _detect_question_column(self, df: pd.DataFrame) -> Optional[str]:
        """Detect the column that contains questions via keyword match"""
        for col in df.columns:
            if any(keyword in str(col).lower() for keyword in self.question_keywords):
                return col
        return None
