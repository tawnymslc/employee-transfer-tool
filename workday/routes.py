from fastapi import APIRouter

router = APIRouter()


@router.post("/events/worker-transfer")
def process_worker_transfer():
    return {"status": "received"}