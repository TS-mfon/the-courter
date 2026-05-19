# { "Depends": "py-genlayer:test" }

import json
from genlayer import *


def _commercial_context(payload: dict) -> dict:
    case_input = payload.get("case_input", {}) or {}
    return {
        "workflow_type": case_input.get("workflow_type", "contract"),
        "counterparty_name": case_input.get("counterparty_name"),
        "contract_reference": case_input.get("contract_reference"),
        "claim_value_summary": case_input.get("claim_value_summary"),
        "agreement_confirmed": bool(case_input.get("agreement_confirmed", False)),
    }


def _decision_copy(winner: str, workflow_type: str) -> tuple[str, str]:
    if winner == "claimant":
        return (
            "The claimant has the stronger documented commercial position.",
            f"The submitted {workflow_type.replace('_', ' ')} record favors the claimant once timeline, documents, and governing rules are weighed together.",
        )
    return (
        "The record is too contested for a unilateral commercial recommendation.",
        f"The submitted {workflow_type.replace('_', ' ')} record contains enough contradiction or evidentiary conflict that a split outcome or negotiated settlement remains more supportable.",
    )


class StandardCourt(gl.Contract):
    owner: Address
    case_count: u256

    def __init__(self):
        self.owner = gl.message.sender_address
        self.case_count = 0

    @gl.public.write
    def submit_case(self, case_payload: str) -> str:
        self.case_count += 1
        return self._finalize(case_payload, "standard_review")

    @gl.public.view
    def get_case_count(self) -> u256:
        return self.case_count

    def _finalize(self, case_payload: str, review_track: str) -> str:
        payload = json.loads(case_payload)
        judgment = payload.get("judgment_draft", {}) or {}
        laws = payload.get("retrieved_laws", []) or []
        judges = payload.get("judge_profiles", []) or []
        contradiction = payload.get("contradiction_report", {}) or {}
        issues = contradiction.get("issues", []) or []
        severity = int(contradiction.get("severity", 0) * 100)
        confidence = 86 - severity
        if confidence < 67:
            confidence = 67
        winner = "claimant"
        if severity >= 55:
            winner = "split"

        context = _commercial_context(payload)
        headline, conclusion = _decision_copy(judgment.get("winner", winner), context["workflow_type"])

        judgment["winner"] = judgment.get("winner", winner)
        judgment["confidence"] = judgment.get("confidence", round(confidence / 100, 2))
        judgment["judges_used"] = judgment.get("judges_used", [judge.get("name", "Profile Unknown") for judge in judges])
        judgment["laws_used"] = judgment.get("laws_used", [law.get("section_id", "UNKNOWN") for law in laws])
        judgment["contradictions"] = judgment.get("contradictions", issues)
        judgment["headline_verdict"] = judgment.get("headline_verdict", headline)
        judgment["final_conclusion"] = judgment.get("final_conclusion", conclusion)
        judgment["reasoning_summary"] = judgment.get("reasoning_summary", [
            "The leader finalized the commercial ADR draft using the submitted evidence, contradiction report, and retrieved rules.",
            "Only the finalized leader result is stored onchain; supporting profile perspectives remain part of the offchain case record.",
            "The resulting decision remains eligible for escalation under the pre-agreed workflow.",
        ])
        judgment["decision_type"] = "commercial_resolution"
        judgment["review_track"] = review_track
        judgment["business_context"] = context
        judgment["appealable"] = True
        judgment["finalized"] = True
        return json.dumps(judgment, sort_keys=True)
