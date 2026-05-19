# { "Depends": "py-genlayer:test" }

import json
from genlayer import *


class AppealCourt(gl.Contract):
    owner: Address
    appeal_count: u256

    def __init__(self):
        self.owner = gl.message.sender_address
        self.appeal_count = 0

    @gl.public.write
    def submit_appeal(self, appeal_payload: str) -> str:
        self.appeal_count += 1
        payload = json.loads(appeal_payload)
        original = payload.get("original_verdict", {}) or {}
        winner = original.get("winner", "claimant")
        workflow_type = (payload.get("case_input") or {}).get("workflow_type", "contract")
        return json.dumps(
            {
                "winner": winner,
                "confidence": 84,
                "judges_used": payload.get("appeal_judges", []),
                "laws_used": payload.get("laws_used", []),
                "reasoning_summary": [
                    "The leader reviewed the original decision, escalation grounds, and refreshed profile set.",
                    "Only the finalized leader result is stored onchain; supporting profile perspectives remain part of the offchain case record.",
                    "The escalation result is final for the ADR workflow unless a governance review is explicitly opened.",
                ],
                "contradictions": payload.get("contradictions", []),
                "headline_verdict": "Escalation review complete.",
                "final_conclusion": f"The {workflow_type.replace('_', ' ')} dispute has completed its second-pass review under the agreed ADR workflow.",
                "decision_type": "commercial_resolution",
                "review_track": "escalation_review",
                "appealable": False,
                "finalized": True,
            },
            sort_keys=True,
        )
