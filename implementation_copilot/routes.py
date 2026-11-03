from fastapi import APIRouter
from .services import analyze_meeting
from .schemas import MeetingAnalysisRequest, ImplementationUpdate

router = APIRouter(
    prefix="/copilot",
    tags=["Implementation Copilot"]
)


@router.get("/")
def copilot_status():
    return {
        "application": "Implementation Copilot",
        "status": "running"
    }

@router.post("/analyze-meeting", response_model=ImplementationUpdate)
def analyze_meeting_route(request: MeetingAnalysisRequest):
    return analyze_meeting(request)