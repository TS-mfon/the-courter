from pydantic import BaseModel
from fastapi import APIRouter

from ..services.payments import verify_payment

router = APIRouter()


class PaymentRequest(BaseModel):
    tx_hash: str
    sender_wallet: str
    recipient_wallet: str
    amount_gen: int
    court_type: str
    finalized: bool = True


@router.post("/verify")
def verify(payload: PaymentRequest) -> dict[str, str | bool]:
    result = verify_payment(**payload.model_dump(), actor_id=payload.sender_wallet)
    return {"ok": result.ok, "message": result.public_message, "reason": result.internal_reason if not result.ok else "verified"}
