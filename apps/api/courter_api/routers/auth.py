from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from ..services.audit import audit
from ..services.repository import repo

router = APIRouter()


class AuthRequest(BaseModel):
    username: str
    recovery_key: str | None = None


@router.post("/create")
def create_user(payload: AuthRequest) -> dict[str, str]:
    user = repo.create_user(payload.username)
    audit("user_created", actor_type="user", actor_id=payload.username, entity_type="user", entity_id=payload.username)
    return user


@router.post("/recover")
def recover_user(payload: AuthRequest) -> dict[str, str]:
    user = repo.get_user(payload.username)
    if not payload.recovery_key or not user or user["recovery_key"] != payload.recovery_key:
        audit("recovery_failed", actor_type="user", actor_id=payload.username, entity_type="user", entity_id=payload.username, severity="warning")
        raise HTTPException(status_code=401, detail="Recovery failed")
    audit("recovery_succeeded", actor_type="user", actor_id=payload.username, entity_type="user", entity_id=payload.username)
    return {"status": "restored", "username": payload.username}
