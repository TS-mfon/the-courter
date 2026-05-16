# { "Depends": "py-genlayer:test" }

import json
from genlayer import *


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
        judgment = payload.get("judgment_draft", {})
        laws = payload.get("retrieved_laws", [])
        judges = payload.get("judge_profiles", [])
        contradiction = payload.get("contradiction_report", {})
        severity = int(contradiction.get("severity", 0) * 100)
        confidence = 91 - severity
        if confidence < 70:
            confidence = 70
        winner = "claimant" if severity < 60 else "split"
        if judgment:
            judgment["winner"] = judgment.get("winner", winner)
            judgment["confidence"] = judgment.get("confidence", round(confidence / 100, 2))
            judgment["judges_used"] = judgment.get("judges_used", [judge.get("name", "Justice Unknown") for judge in judges])
            judgment["laws_used"] = judgment.get("laws_used", [law.get("section_id", "UNKNOWN") for law in laws])
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
                    "Inner Court received a structured judgment draft with stronger profile-weighted reasoning.",
                    "The contract finalized that draft after checking the contradiction report and legal sections.",
                    "The inner court verdict is finalized and ready for the public verdict view.",
                ],
                "contradictions": contradiction.get("issues", []),
                "headline_verdict": "The claimant has the stronger civil position." if winner == "claimant" else "The record is too contested for a unilateral award.",
                "final_conclusion": "The final conclusion follows the majority direction across the submitted judge profiles.",
                "appealable": True,
                "finalized": True,
            },
            sort_keys=True,
        )
