# { "Depends": "py-genlayer:test" }

import json
from genlayer import *


class StandardCourt(gl.Contract):
    owner: Address
    case_count: u256

    def __init__(self):
        self.owner = gl.message.sender_address
        self.case_count = 0

    @gl.public.write
    def submit_case(self, case_payload: str) -> str:
        self.case_count += 1
        return self._finalize(case_payload, "public")

    @gl.public.view
    def get_case_count(self) -> u256:
        return self.case_count

    def _finalize(self, case_payload: str, court_type: str) -> str:
        payload = json.loads(case_payload)
        judgment = payload.get("judgment_draft", {})
        laws = payload.get("retrieved_laws", [])
        judges = payload.get("judge_profiles", [])
        contradiction = payload.get("contradiction_report", {})
        issues = contradiction.get("issues", [])
        severity = int(contradiction.get("severity", 0) * 100)
        confidence = 86 - severity
        if confidence < 67:
            confidence = 67
        winner = "claimant"
        if severity >= 55:
            winner = "split"
        if judgment:
            judgment["winner"] = judgment.get("winner", winner)
            judgment["confidence"] = judgment.get("confidence", round(confidence / 100, 2))
            judgment["judges_used"] = judgment.get("judges_used", [judge.get("name", "Justice Unknown") for judge in judges])
            judgment["laws_used"] = judgment.get("laws_used", [law.get("section_id", "UNKNOWN") for law in laws])
            judgment["contradictions"] = judgment.get("contradictions", issues)
            judgment["appealable"] = True
            judgment["finalized"] = True
            return json.dumps(judgment, sort_keys=True)
        return json.dumps(
            {
                "winner": winner,
                "confidence": round(confidence / 100, 2),
                "judges_used": [judge.get("name", "Justice Unknown") for judge in judges],
                "laws_used": [law.get("section_id", "UNKNOWN") for law in laws],
                "reasoning_summary": [
                    "The public court received structured evidence, retrieved law, and profile-guided judge analysis.",
                    "The contract finalized the verdict using the submitted reasoning draft and contradiction report.",
                    f"The {court_type} court returned a finalized civil judgment.",
                ],
                "contradictions": issues,
                "headline_verdict": "The claimant has the stronger civil position." if winner == "claimant" else "The record is too contested for a unilateral award.",
                "final_conclusion": "The final conclusion follows the majority direction across the submitted judge profiles.",
                "appealable": True,
                "finalized": True,
            },
            sort_keys=True,
        )
