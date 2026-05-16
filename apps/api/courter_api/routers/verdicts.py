from fastapi import APIRouter
from fastapi import HTTPException

from ..services.repository import repo

router = APIRouter()


@router.get("/{case_id}")
def get_verdict(case_id: str) -> dict[str, str | bool]:
    record = repo.get_case(case_id)
    if not record:
        raise HTTPException(status_code=404, detail="Case not found")
    return {"case_id": case_id, "status": record["status"], "finalized": record.get("verdict", {}).get("finalized") is True, "verdict": record.get("verdict"), "genlayer": record.get("genlayer")}
