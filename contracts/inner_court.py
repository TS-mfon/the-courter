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
            f"The submitted {workflow_type.replace('_', ' ')} record supports the claimant after a higher-scrutiny review of evidence quality, chronology, and cited rules.",
        )
    return (
        "The record is too contested for a unilateral commercial recommendation.",
        f"The submitted {workflow_type.replace('_', ' ')} record remains too contested even after a higher-scrutiny review, so a split outcome or negotiated settlement remains more supportable.",
    )


class InnerCourt(gl.Contract):
    owner: Address
    case_count: u256

    def __init__(self):
        self.owner = gl.message.sender_address
        self.case_count = 0

    @gl.public.write
    def submit_inner_case(self, case_payload: str) -> str:
        self.case_count += 1
        payload = json.loads(case_payload)
        judgment = payload.get("judgment_draft", {}) or {}
        laws = payload.get("retrieved_laws", []) or []
        judges = payload.get("judge_profiles", []) or []
        contradiction = payload.get("contradiction_report", {}) or {}
        severity = int(contradiction.get("severity", 0) * 100)
        confidence = 91 - severity
        if confidence < 70:
            confidence = 70
        winner = "claimant" if severity < 60 else "split"

        context = _commercial_context(payload)
        final_winner = judgment.get("winner", winner)
        headline, conclusion = _decision_copy(final_winner, context["workflow_type"])

        judgment["winner"] = final_winner
        judgment["confidence"] = judgment.get("confidence", round(confidence / 100, 2))
        judgment["judges_used"] = judgment.get("judges_used", [judge.get("name", "Profile Unknown") for judge in judges])
        judgment["laws_used"] = judgment.get("laws_used", [law.get("section_id", "UNKNOWN") for law in laws])
        judgment["contradictions"] = judgment.get("contradictions", contradiction.get("issues", []))
        judgment["headline_verdict"] = judgment.get("headline_verdict", headline)
        judgment["final_conclusion"] = judgment.get("final_conclusion", conclusion)
        judgment["reasoning_summary"] = judgment.get("reasoning_summary", [
            "The leader finalized the complex commercial ADR draft using a higher-confidence review track.",
            "Only the finalized leader result is stored onchain; supporting profile perspectives remain part of the offchain case record.",
            "The resulting decision remains eligible for escalation under the pre-agreed workflow.",
        ])
        judgment["decision_type"] = "commercial_resolution"
        judgment["review_track"] = "complex_review"
        judgment["business_context"] = context
        judgment["appealable"] = True
        judgment["finalized"] = True
        return json.dumps(judgment, sort_keys=True)
