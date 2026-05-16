from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from courter_shared.schemas import CaseIntake

from ..config import get_settings
from ..services.audit import audit
from ..services.courts import deliberate_case
from ..services.evidence import detect_contradictions, structure_text_evidence
from ..services.genlayer_service import finalized_receipt, write_contract
from ..services.payments import verify_payment
from ..services.repository import repo
from ..services.retrieval import retrieve_legal_chunks

router = APIRouter()


class AppealRequest(BaseModel):
    case_id: str
    username: str
    grounds: str
    tx_hash: str
    sender_wallet: str


@router.post("/")
def create_appeal(payload: AppealRequest) -> dict:
    original = repo.get_case(payload.case_id)
    if not original:
        raise HTTPException(status_code=404, detail="Case not found")
    payment = verify_payment(
        tx_hash=payload.tx_hash,
        sender_wallet=payload.sender_wallet,
        recipient_wallet=get_settings().treasury_wallet,
        amount_gen=5,
        court_type="appeal",
        actor_id=payload.username,
    )
    if not payment.ok:
        raise HTTPException(status_code=402, detail=payment.public_message)
    original_judges = {item.lower().replace(" ", "_") for item in original["verdict"]["judges_used"]}
    case = CaseIntake(
        username=payload.username,
        country=original["country"],
        dispute_type=original["dispute_type"],
        court_type="appeal",
        claimant_statement=payload.grounds,
    )
    evidence = [structure_text_evidence(payload.grounds, original["country"])]
    contradiction = detect_contradictions(evidence)
    chunks = retrieve_legal_chunks(original["country"], original["dispute_type"], limit=8)
    verdict, reasoning = deliberate_case(case, evidence, contradiction, chunks, excluded_judges=original_judges)
    contract_payload = {"original_case": original, "appeal_grounds": payload.grounds, "appeal_verdict": verdict.model_dump(), "judge_reasoning": reasoning}
    write = write_contract("appeal", "submit_appeal", contract_payload, payload.case_id)
    receipt = finalized_receipt(write["tx_hash"], payload.case_id)
    original["status"] = "appealed"
    original["appeal"] = {"grounds": payload.grounds, "verdict": verdict.model_dump(), "judge_reasoning": reasoning, "genlayer": {"write": write, "receipt": receipt}}
    repo.save_case(original)
    audit("appeal_created", actor_type="user", actor_id=payload.username, entity_type="case", entity_id=payload.case_id, metadata={"tx_hash": payload.tx_hash})
    return original["appeal"]
