from fastapi import APIRouter

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