from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from courter_shared.schemas import CaseIntake
from courter_shared.constants import COURT_FEES_GEN

from ..config import get_settings
from ..services.audit import audit
from ..services.courts import create_case_record, public_case_record, reject_criminal_case
from ..services.evidence import detect_contradictions, evidence_quality, extract_text, fraud_report, reconstruct_timeline, structure_text_evidence
from ..services.payments import consume_verified_payment, verify_payment
from ..services.repository import repo

router = APIRouter()


@router.post("/")
def create_case(case: CaseIntake) -> dict:
    if reject_criminal_case(case):
        audit("case_rejected", actor_type="user", actor_id=case.username, entity_type="case", entity_id="draft", severity="warning", metadata={"reason": "criminal_or_violent"})
        raise HTTPException(status_code=400, detail="The Courter only supports civil arbitration.")
    quality = evidence_quality(case.claimant_statement, 0)
    if not quality["acceptable"]:
        audit("case_rejected", actor_type="user", actor_id=case.username, entity_type="case", entity_id="draft", severity="warning", metadata={"reason": "insufficient_evidence", "quality": quality})
        raise HTTPException(status_code=400, detail={"message": "The Jury cannot review empty or vague claims. Add real civil facts, dates, document names, registry IDs, payments, or upload evidence.", "quality": quality})
    evidence = [structure_text_evidence(case.claimant_statement, case.country)]
    contradiction = detect_contradictions(evidence)
    record = create_case_record(case=case, evidence=evidence, contradiction=contradiction, extracted_files=[], timeline=reconstruct_timeline(case.claimant_statement), fraud=fraud_report(evidence, case.claimant_statement))
    return record


@router.post("/submit")
async def submit_case(
    username: str = Form(...),
    country: str = Form(...),
    dispute_type: str = Form(...),
    court_type: str = Form("public"),
    claimant_statement: str = Form(...),
    respondent_statement: str = Form(""),
    evidence_summary: str = Form(""),
    tx_hash: str = Form(...),
    sender_wallet: str = Form(...),
    files: list[UploadFile] = File(default=[]),
) -> dict:
    settings = get_settings()
    user = repo.get_user(username)
    if not user:
        user = repo.create_user(username)
        audit("user_created", actor_type="user", actor_id=username, entity_type="user", entity_id=username, metadata={"created_during_case_submit": True})

    case = CaseIntake(
        username=username,
        country=country.lower(),
        dispute_type=dispute_type.lower().replace(" ", "_"),
        court_type=court_type,
        claimant_statement=claimant_statement,
        respondent_statement=respondent_statement,
    )
    if reject_criminal_case(case):
        raise HTTPException(status_code=400, detail="The Courter only supports civil arbitration.")

    pre_payment_quality = evidence_quality(" ".join([claimant_statement, respondent_statement, evidence_summary]), len(files))
    if not pre_payment_quality["acceptable"]:
        audit("case_rejected", actor_type="user", actor_id=username, entity_type="case", entity_id="draft", severity="warning", metadata={"reason": "insufficient_evidence", "quality": pre_payment_quality})
        raise HTTPException(status_code=400, detail={"message": "The Jury cannot review empty or vague claims. Add real civil facts, dates, document names, registry IDs, payments, or supporting uploads before paying.", "quality": pre_payment_quality})

    amount = COURT_FEES_GEN.get(court_type, 2)
    payment = verify_payment(
        tx_hash=tx_hash,
        sender_wallet=sender_wallet,
        recipient_wallet=settings.treasury_wallet,
        amount_gen=amount,
        court_type=court_type,
        actor_id=username,
        consume=False,
    )
    if not payment.ok:
        raise HTTPException(status_code=402, detail=payment.public_message)

    extracted = []
    for file in files:
        try:
            extracted.append(await extract_text(file, "draft", username))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    combined_text = " ".join([claimant_statement, respondent_statement, evidence_summary] + [item["text"] for item in extracted])
    post_ocr_quality = evidence_quality(combined_text, len(extracted))
    if not post_ocr_quality["acceptable"]:
        audit("case_rejected", actor_type="user", actor_id=username, entity_type="case", entity_id="draft", severity="warning", metadata={"reason": "insufficient_evidence_after_ocr", "quality": post_ocr_quality})
        raise HTTPException(status_code=400, detail={"message": "Evidence upload/OCR did not produce enough civil facts for judicial review.", "quality": post_ocr_quality})
    evidence = [structure_text_evidence(combined_text, country)]
    contradiction = detect_contradictions(evidence)
    record = create_case_record(
        case=case,
        evidence=evidence,
        contradiction=contradiction,
        extracted_files=extracted,
        timeline=reconstruct_timeline(combined_text),
        fraud=fraud_report(evidence, combined_text),
    )
    consumption = consume_verified_payment(payment=payment.payment or {}, actor_id=username)
    if not consumption.ok:
        raise HTTPException(status_code=402, detail=consumption.public_message)
    audit("case_submitted", actor_type="user", actor_id=username, entity_type="case", entity_id=record["id"], metadata={"court_type": court_type, "files": len(files)})
    return record


@router.get("/")
def list_cases(public: bool = False) -> dict:
    return {"cases": [public_case_record(case) for case in repo.list_cases(public_only=public)]}


@router.get("/{case_id}")
def get_case(case_id: str) -> dict:
    record = repo.get_case(case_id)
    if not record:
        raise HTTPException(status_code=404, detail="Case not found")
    return public_case_record(record)
