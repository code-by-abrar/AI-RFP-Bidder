# backend/app/routes/questionnaire_routes.py

import os
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import FileResponse
from backend.app.agents.agent7_questionnaire_filler import QuestionnaireFillerAgent
from backend.app.middleware.auth import get_current_user
import shutil
from uuid import uuid4

router = APIRouter(prefix="/api/questionnaire", tags=["Questionnaire"])

@router.post("/fill")
async def fill_questionnaire(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    """
    Accepts an Excel file containing a questionnaire, uses the RAG + LLM to fill answers,
    and returns the populated Excel file.
    """
    
    # Validate extension
    ext = file.filename.split('.')[-1].lower() if file.filename else ""
    if ext not in ["xlsx", "xls"]:
        raise HTTPException(status_code=400, detail="Only .xlsx or .xls Excel files are supported")
        
    # Save the uploaded file temporarily
    os.makedirs(".data/uploads", exist_ok=True)
    temp_path = f".data/uploads/questionnaire_{uuid4().hex[:8]}.{ext}"
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Instantiate the agent
        agent = QuestionnaireFillerAgent()
        
        # Process the file
        output_file_path = await agent.process_excel_questionnaire(
            file_path=temp_path,
            company_id=str(current_user.company_id)
        )
        
        # Determine clean download filename
        download_name = file.filename.replace(f".{ext}", "_Filled.xlsx")
        
        # Return the populated file as a download
        return FileResponse(
            path=output_file_path,
            filename=download_name,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # We don't delete the output file yet because FileResponse needs to stream it,
        # but Fastapi handles background cleanup or we can leave it in .data/exports for now.
        pass
