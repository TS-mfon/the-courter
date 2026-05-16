from fastapi import APIRouter

router = APIRouter()


@router.post("/event")
def notify(payload: dict) -> dict[str, str]:
    return {"status": "queued"}
