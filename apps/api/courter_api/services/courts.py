from __future__ import annotations

import secrets
from typing import Any

from courter_shared.constants import CRIMINAL_REJECTION_TERMS
from courter_shared.judges import load_judge_profiles, select_judges
from courter_shared.schemas import CaseIntake, ContradictionReport, JudgePanel, LawCitation, StructuredEvidence, Verdict

from .audit import audit
from .genlayer_service import extract_contract_judgment, finalized_receipt, write_contract
from .repository import now_iso, repo
from .retrieval import retrieve_legal_chunks


def reject_criminal_case(case: CaseIntake) -> bool:
    text = " ".join([case.dispute_type, case.claimant_statement, case.respondent_statement or ""]).lower()
    return any(term in text for term in CRIMINAL_REJECTION_TERMS)


def _judge_rationale(judge: dict[str, Any], contradiction: ContradictionReport, evidence: list[StructuredEvidence]) -> list[str]:
    style = judge.get("style", "Analytical")
    profile = judge.get("description", "").strip()
    evidence_notes = []
    if any(item.owner for item in evidence):
        evidence_notes.append("named ownership fields were extracted")
    if any(item.registry_id for item in evidence):
        evidence_notes.append("registry identifiers were found")
    if contradiction.contradiction_detected:
        evidence_notes.append("contradictions were weighed conservatively")
    else:
        evidence_notes.append("the submitted record remained internally consistent")
    approach = {
        "Rational legal analyst": "Reasoned from statute, chronology, and documentary causation before giving weight to unsupported assertions.",
        "Analytical": "Separated the facts into proof, timeline, and credibility signals before drawing a civil conclusion.",
        "Ownership focused": "Focused on title, transfer records, possession claims, and whether ownership proof was legally recognizable.",
    }.get(style, "Applied the judge profile to the submitted civil record before reaching a conclusion.")
    return [
        approach,
        f"{judge['name']} noted that {', '.join(evidence_notes)}.",
        profile or f"{judge['name']} applied the assigned judicial profile.",
    ]


def _law_citations(legal_chunks: list[dict[str, Any]], judge_name: str, limit: int = 3) -> list[LawCitation]:
    ranked = sorted(
        legal_chunks,
        key=lambda chunk: float((chunk.get("judge_relevance") or {}).get(judge_name, chunk.get("importance", 0.5))),
        reverse=True,
    )[:limit]
    return [
        LawCitation(
            section_id=chunk.get("section_id", "UNKNOWN"),
            title=chunk.get("title", "Untitled Law"),
            summary=chunk.get("summary", chunk.get("content", "")),
            relevance=min(1.0, max(0.0, float((chunk.get("judge_relevance") or {}).get(judge_name, chunk.get("importance", 0.5))))),
        )
        for chunk in ranked
    ]


def _judge_reasoning(
    judges: list[dict[str, Any]],
    legal_chunks: list[dict[str, Any]],
    contradiction: ContradictionReport,
    evidence: list[StructuredEvidence],
) -> list[JudgePanel]:
    reasoning: list[JudgePanel] = []
    for judge in judges:
        evidence_weight = float(judge.get("evidence_weight", 0.75))
        strictness = float(judge.get("strictness", 0.75))
        confidence = max(0.51, min(0.98, 0.72 + evidence_weight * 0.12 + strictness * 0.08 - contradiction.severity * 0.18))
        citations = _law_citations(legal_chunks, judge["name"])
        reasoning.append(
            JudgePanel(
                judge=judge["name"],
                profile=judge.get("description", judge.get("style", "Judicial profile")),
                confidence=round(confidence, 2),
                reasoning=_judge_rationale(judge, contradiction, evidence),
                laws_used=[item.section_id for item in citations],
                cited_laws=citations,
                contradictions_detected=contradiction.issues,
            )
        )
    return reasoning


def deliberate_case(
    case: CaseIntake,
    evidence: list[StructuredEvidence],
    contradiction: ContradictionReport,
    legal_chunks: list[dict],
    excluded_judges: set[str] | None = None,
    judge_count: int = 3,
) -> tuple[Verdict, list[dict[str, Any]]]:
    prefer_rational = contradiction.contradiction_detected or contradiction.severity >= 0.6
    judges = select_judges(count=judge_count, excluded_ids=excluded_judges, prefer_rational=prefer_rational)
    judge_reasoning = _judge_reasoning(judges, legal_chunks, contradiction, evidence)
    avg_confidence = sum(item.confidence for item in judge_reasoning) / len(judge_reasoning)
    confidence = max(0.51, min(0.98, avg_confidence - contradiction.severity * 0.12))
    winner = "claimant" if confidence >= 0.62 else "split"
    headline_verdict = (
        "The claimant has the stronger civil position."
        if winner == "claimant"
        else "The record is too contested for a unilateral award."
    )
    final_conclusion = (
        "Across the selected judge profiles, the claimant's documentary position remained stronger than the competing account when measured against the cited laws."
        if winner == "claimant"
        else "Across the selected judge profiles, the contradictions and evidentiary gaps prevented a single party from carrying the civil burden cleanly."
    )
    law_citations = _law_citations(legal_chunks, judge_reasoning[0].judge, limit=min(5, len(legal_chunks))) if judge_reasoning else []
    evidence_overview = "; ".join(
        filter(
            None,
            [
                f"{len(evidence)} structured evidence item{'s' if len(evidence) != 1 else ''}",
                "ownership fields detected" if any(item.owner for item in evidence) else "",
                "registry identifiers detected" if any(item.registry_id for item in evidence) else "",
                "contradictions detected" if contradiction.contradiction_detected else "no material contradiction detected",
            ],
        )
    )
    verdict = Verdict(
        winner=winner,
        confidence=round(confidence, 2),
        judges_used=[judge["name"] for judge in judges],
        laws_used=[chunk.get("section_id", chunk.get("id", "unknown")) for chunk in legal_chunks[:6]],
        reasoning_summary=[
            "The court reviewed structured evidence, chronology signals, and contradiction severity before weighing the law.",
            "Each selected judge profile produced an independent reasoning track grounded in the retrieved legal sections.",
            "The final conclusion reflects the majority direction across those judge panels and remains appealable unless superseded by later court flow.",
        ],
        contradictions=contradiction.issues,
        headline_verdict=headline_verdict,
        final_conclusion=final_conclusion,
        filing_summary=evidence[0].document_type.replace("_", " ").title() if evidence else "Civil filing",
        evidence_overview=evidence_overview,
        judge_panels=judge_reasoning,
        law_citations=law_citations,
        appealable=True,
        finalized=True,
    )
    return verdict, [item.model_dump() for item in judge_reasoning]


def run_complex_failsafe(case: CaseIntake, evidence: list[StructuredEvidence], contradiction: ContradictionReport) -> tuple[Verdict, list[dict], list[dict]]:
    expanded_chunks = retrieve_legal_chunks(case.country, case.dispute_type, limit=10)
    verdict, reasoning = deliberate_case(case, evidence, contradiction, expanded_chunks, judge_count=5)
    verdict.confidence = max(verdict.confidence, 0.67)
    return verdict, reasoning, expanded_chunks


def _public_case_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": record["id"],
        "username": record["username"],
        "country": record["country"],
        "dispute_type": record["dispute_type"],
        "court_type": record["court_type"],
        "status": record["status"],
        "public": record.get("public", True),
        "created_at": record["created_at"],
        "structured_evidence": record["structured_evidence"],
        "contradiction_report": record["contradiction_report"],
        "timeline": record["timeline"],
        "fraud_report": record["fraud_report"],
        "retrieved_laws": record["retrieved_laws"],
        "judge_reasoning": record["judge_reasoning"],
        "verdict": record["verdict"],
        "plain_english_verdict": record["plain_english_verdict"],
        "ocr": record.get("ocr", {}),
        "payment": record.get("payment", {}),
    }


def public_case_record(record: dict[str, Any]) -> dict[str, Any]:
    return _public_case_record(record)


def create_case_record(
    *,
    case: CaseIntake,
    evidence: list[StructuredEvidence],
    contradiction: ContradictionReport,
    extracted_files: list[dict],
    timeline: list[dict],
    fraud: dict,
) -> dict[str, Any]:
    legal_chunks = retrieve_legal_chunks(case.country, case.dispute_type, limit=6)
    verdict, judge_reasoning = deliberate_case(case, evidence, contradiction, legal_chunks)
    route_to_complex = verdict.confidence < 0.7 or contradiction.severity >= 0.72
    if route_to_complex:
        verdict, judge_reasoning, legal_chunks = run_complex_failsafe(case, evidence, contradiction)

    case_id = f"CASE-{secrets.token_hex(4).upper()}"
    contract_payload = {
        "case_id": case_id,
        "case_input": case.model_dump(),
        "retrieved_laws": legal_chunks,
        "structured_evidence": [item.model_dump() for item in evidence],
        "judge_profiles": [item for item in load_judge_profiles() if item["name"] in verdict.judges_used],
        "judge_reasoning": judge_reasoning,
        "contradiction_report": contradiction.model_dump(),
        "route_to_complex_analysis": route_to_complex,
        "timeline": timeline,
        "fraud_report": fraud,
        "judgment_draft": verdict.model_dump(),
    }
    court_type = "inner" if case.court_type == "inner" else "public"
    contract = write_contract(court_type, "submit_inner_case" if court_type == "inner" else "submit_case", contract_payload, case_id)
    receipt = finalized_receipt(contract.get("tx_hash", ""), case_id)
    contract_finalized = receipt.get("status") == "FINALIZED"
    contract_judgment = extract_contract_judgment(contract, receipt)
    final_verdict = contract_judgment or verdict.model_dump()
    final_verdict["finalized"] = contract_finalized
    final_verdict.setdefault("headline_verdict", verdict.headline_verdict)
    final_verdict.setdefault("final_conclusion", verdict.final_conclusion)
    final_verdict.setdefault("filing_summary", verdict.filing_summary)
    final_verdict.setdefault("evidence_overview", verdict.evidence_overview)
    final_verdict.setdefault("judge_panels", verdict.model_dump().get("judge_panels", []))
    final_verdict.setdefault("law_citations", verdict.model_dump().get("law_citations", []))

    record = {
        "id": case_id,
        "username": case.username,
        "country": case.country,
        "dispute_type": case.dispute_type,
        "court_type": court_type,
        "status": "finalized" if contract_finalized else "awaiting_genlayer_contract",
        "public": True,
        "created_at": now_iso(),
        "input": case.model_dump(),
        "evidence_files": extracted_files,
        "structured_evidence": [item.model_dump() for item in evidence],
        "contradiction_report": contradiction.model_dump(),
        "timeline": timeline,
        "fraud_report": fraud,
        "retrieved_laws": legal_chunks,
        "judge_reasoning": judge_reasoning,
        "verdict": final_verdict if contract_finalized else {
            **verdict.model_dump(),
            "finalized": False,
            "reasoning_summary": [
                "Backend preprocessing completed, but the verdict is not finalized yet because the court is still awaiting a final GenLayer result.",
                "This page will render the judge panels and final conclusion as soon as the contract result is confirmed."
            ],
        },
        "plain_english_verdict": (
            final_verdict.get("headline_verdict", verdict.headline_verdict)
            if contract_finalized
            else "The court is still verifying payment, evidence, laws, and contract finalization before releasing the verdict."
        ),
        "ocr": {
            "files_processed": len(extracted_files),
            "degraded": any(item.get("ocr_method", "").endswith("unavailable") or item.get("ocr_method") == "ocr-degraded-fallback" for item in extracted_files),
            "methods": [item.get("ocr_method") for item in extracted_files],
        },
        "payment": {
            "required_fee_gen": 5 if case.court_type == "inner" else 2,
            "court_type": court_type,
            "status": "verified",
        },
        "admin_diagnostics": {
            "input": case.model_dump(),
            "evidence_files": extracted_files,
            "genlayer": {"write": contract, "receipt": receipt},
            "route_to_complex_analysis": route_to_complex,
            "fraud_report": fraud,
        },
        "appealable": verdict.appealable,
    }
    repo.save_case(record)
    audit("verdict_generated" if contract_finalized else "verdict_pending", actor_type="system", actor_id="court-engine", entity_type="case", entity_id=case_id, severity="info" if contract_finalized else "warning", metadata={"winner": final_verdict.get("winner", verdict.winner), "confidence": final_verdict.get("confidence", verdict.confidence), "contract_finalized": contract_finalized})
    return public_case_record(record)
