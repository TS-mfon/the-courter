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
        original = payload.get("original_verdict", {})
        winner = original.get("winner", "claimant")
        return json.dumps(
            {
                "winner": winner,
                "confidence": 84,
                "judges_used": payload.get("appeal_judges", []),
                "laws_used": payload.get("laws_used", []),
                "reasoning_summary": [
                    "Appeal Court reviewed the original finalized verdict and appeal payload.",
                    "Appeal judges are expected to differ from the original panel.",
                    "The appeal verdict is finalized and remains eligible for Shadow Council escalation.",
                ],
                "contradictions": payload.get("contradictions", []),
                "appealable": False,
                "finalized": True,
            },
            sort_keys=True,
        )
