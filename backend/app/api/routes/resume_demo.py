from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.demos.resume_assistant.orchestrator import orchestrator

router = APIRouter()


class ResumeRequest(BaseModel):
    user_input: str
    job_description: str

@router.post("/resume-builder/generate")
async def generate_resume(request: ResumeRequest):
    """
    Trigger the Multi-Agent Resume Builder.
    """

    try:
        result = orchestrator(
            user_input=request.user_input,
            job_description=request.job_description
        )
        return {"result": result}
    except Exception as e:
        print(f"Error in resume generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))