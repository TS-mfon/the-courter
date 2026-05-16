from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..config import get_settings
from ..services.audit import audit
from ..services.genlayer_service import finalized_receipt, write_contract
from ..services.payments import verify_payment
from ..services.repository import now_iso, repo

router = APIRouter()


class ProposalRequest(BaseModel):
    case_id: str
    username: str
    tx_hash: str
    sender_wallet: str


class VoteRequest(BaseModel):
    proposal_id: str
    wallet: str
    vote: str


@router.get("/members")
def members() -> dict:
    return {"members": repo.list_council_members()}


@router.get("/proposals")
def proposals() -> dict:
    return {"proposals": repo.list_proposals()}


@router.post("/proposals")
def create_proposal(payload: ProposalRequest) -> dict:
    case = repo.get_case(payload.case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    payment = verify_payment(
        tx_hash=payload.tx_hash,
        sender_wallet=payload.sender_wallet,
        recipient_wallet=get_settings().treasury_wallet,
        amount_gen=10,
        court_type="shadow_council",
        actor_id=payload.username,
    )
    if not payment.ok:
        raise HTTPException(status_code=402, detail=payment.public_message)
    proposal = {
        "id": f"PROP-{secrets.token_hex(4).upper()}",
        "case_id": payload.case_id,
        "current_verdict": case["verdict"]["winner"],
        "reasoning": case["verdict"]["reasoning_summary"],
        "status": "active",
        "yes_weight": 0,
        "no_weight": 0,
        "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "votes": [],
        "created_at": now_iso(),
    }
    write = write_contract("shadow_council", "create_proposal", proposal, payload.case_id)
    proposal["genlayer"] = {"write": write}
    repo.save_proposal(proposal)
    audit("shadow_proposal_created", actor_type="user", actor_id=payload.username, entity_type="proposal", entity_id=proposal["id"], metadata={"case_id": payload.case_id})
    return proposal


@router.post("/vote")
def vote(payload: VoteRequest) -> dict:
    proposals = {proposal["id"]: proposal for proposal in repo.list_proposals()}
    proposal = proposals.get(payload.proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    if proposal["status"] != "active":
        raise HTTPException(status_code=409, detail="Proposal is closed")
    member = next((item for item in repo.list_council_members() if item["wallet"].lower() == payload.wallet.lower() and item["active"]), None)
    if not member:
        raise HTTPException(status_code=403, detail="Only For Council Members")
    if any(item["wallet"].lower() == payload.wallet.lower() for item in proposal["votes"]):
        raise HTTPException(status_code=409, detail="Wallet has already voted")
    choice = payload.vote.upper()
    if choice not in {"YES", "NO"}:
        raise HTTPException(status_code=400, detail="Vote must be YES or NO")
    vote_record = {"wallet": payload.wallet, "vote": choice, "weight": member["voting_weight"], "timestamp": now_iso()}
    proposal["votes"].append(vote_record)
    if choice == "YES":
        proposal["yes_weight"] += member["voting_weight"]
    else:
        proposal["no_weight"] += member["voting_weight"]
    active_total = sum(item["voting_weight"] for item in repo.list_council_members() if item["active"])
    cast_total = proposal["yes_weight"] + proposal["no_weight"]
    remaining = active_total - cast_total
    if proposal["yes_weight"] > proposal["no_weight"] + remaining or proposal["no_weight"] >= proposal["yes_weight"] + remaining:
        proposal["status"] = "upheld" if proposal["yes_weight"] > proposal["no_weight"] else "overruled"
        proposal["final_message"] = "You Have Been Saved By The Shadow Council" if proposal["status"] == "overruled" else "Verdict upheld by the Shadow Council"
        receipt = finalized_receipt(proposal["genlayer"]["write"]["tx_hash"], proposal["case_id"])
        proposal["genlayer"]["receipt"] = receipt
    repo.save_proposal(proposal)
    audit("council_vote_cast", actor_type="council_member", actor_id=payload.wallet, entity_type="proposal", entity_id=payload.proposal_id, metadata=vote_record)
    return proposal
