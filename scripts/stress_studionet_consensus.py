from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from eth_account import Account
from genlayer_py.chains.studionet import studionet
from genlayer_py.client import create_client

from deploy_studionet_contracts import patch_web3_contract_fn_compat, wait_finalized


ROOT = Path(__file__).resolve().parents[1]


def case_payload(position: str, contradiction_severity: float = 0.0) -> str:
    if position == "claimant":
        claimant = "Signed delivery note and invoice show complete delivery and overdue payment."
        respondent = "Respondent alleges delay but provides no rejection notice or contrary record."
        draft_winner = "claimant"
    elif position == "respondent":
        claimant = "Claimant requests payment but provides no signed acceptance or completion record."
        respondent = "Signed defect notices, rejection emails, and remediation logs show non-performance."
        draft_winner = "respondent"
    else:
        claimant = "Claimant provides an invoice and partial delivery record."
        respondent = "Respondent provides a timely rejection notice and evidence of partial defects."
        draft_winner = "split"

    payload = {
        "case_id": f"STRESS-{position.upper()}",
        "case_input": {
            "username": "consensus_stress",
            "country": "nigeria",
            "dispute_type": "procurement",
            "court_type": "public",
            "claimant_statement": claimant,
            "respondent_statement": respondent,
            "workflow_type": "procurement",
            "counterparty_name": "Stress Counterparty",
            "contract_reference": "PO-STRESS-001",
            "claim_value_summary": "Milestone payment",
            "agreement_confirmed": True,
        },
        "structured_evidence": [
            {
                "document_type": "commercial_record",
                "country": "nigeria",
                "owner": None,
                "registry_id": "PO-STRESS-001",
                "confidence": 0.9,
                "issues_detected": [],
            }
        ],
        "retrieved_laws": [
            {
                "section_id": "NIG-CON-005",
                "title": "Breach of Contract Section 5",
                "summary": "A party seeking relief must prove agreement, breach, and measurable loss.",
                "content": "Documentary proof and performance records determine whether an obligation was breached.",
            }
        ],
        "contradiction_report": {
            "contradiction_detected": contradiction_severity > 0,
            "severity": contradiction_severity,
            "issues": ["Parties dispute acceptance and completion"] if contradiction_severity > 0 else [],
        },
        "timeline": [{"year": "2026", "event": "Delivery and acceptance period"}],
        "fraud_report": {"suspicious": False, "signals": [], "severity": 0},
        "judge_reasoning": [],
        "judgment_draft": {
            "winner": draft_winner,
            "confidence": 0.8,
            "judges_used": ["Stress Review Profile"],
            "laws_used": ["NIG-CON-005"],
            "reasoning_summary": ["Draft prepared for consensus stress test."],
            "contradictions": [],
            "headline_verdict": "Draft commercial decision.",
            "final_conclusion": "Draft conclusion.",
            "filing_summary": "Procurement dispute",
            "evidence_overview": "Structured commercial records",
            "judge_panels": [],
            "law_citations": [],
            "appealable": True,
            "finalized": False,
        },
    }
    return json.dumps(payload, sort_keys=True)


def appeal_payload() -> str:
    return json.dumps(
        {
            "case_input": {"workflow_type": "procurement", "contract_reference": "PO-STRESS-001"},
            "original_verdict": {
                "winner": "claimant",
                "confidence": 0.81,
                "headline_verdict": "Claimant proved delivery and overdue payment.",
                "final_conclusion": "Signed acceptance supported the claimant.",
                "judges_used": ["Stress Review Profile"],
                "laws_used": ["NIG-CON-005"],
            },
            "appeal_grounds": "Respondent alleges the signed acceptance was conditional but supplies no new document.",
            "appeal_verdict": {},
            "appeal_judges": ["Stress Escalation Profile"],
            "laws_used": ["NIG-CON-005"],
            "contradictions": [],
            "judge_reasoning": [],
        },
        sort_keys=True,
    )


def execute(client, address: str, method: str, payload: str, label: str) -> dict:
    tx_hash = client.write_contract(address=address, function_name=method, args=[payload])
    receipt = wait_finalized(tx_hash)
    data = receipt.get("data") or {}
    result_name = receipt.get("result_name") or data.get("result_name")
    execution_result = data.get("execution_result")
    if receipt.get("status") != "FINALIZED":
        raise RuntimeError(f"{label} did not finalize: {tx_hash}")
    if execution_result == "ERROR":
        raise RuntimeError(f"{label} execution error: {data.get('stderr')}")
    if result_name in ("NO_MAJORITY", "UNDETERMINED"):
        raise RuntimeError(f"{label} consensus failed with {result_name}: {tx_hash}")
    return {
        "label": label,
        "tx_hash": tx_hash,
        "status": receipt.get("status"),
        "result_name": result_name,
        "execution_result": execution_result,
    }


def main() -> None:
    load_dotenv(ROOT / ".env.test")
    patch_web3_contract_fn_compat()
    private_key = os.environ.get("GENLAYER_OPERATOR_PRIVATE_KEY") or os.environ["GENLAYER_PRIVATE_KEY"]
    client = create_client(chain=studionet, account=Account.from_key(private_key))
    standard = os.environ["GENLAYER_STANDARD_COURT_ADDRESS"]
    inner = os.environ["GENLAYER_INNER_COURT_ADDRESS"]
    appeal = os.environ["GENLAYER_APPEAL_COURT_ADDRESS"]

    scenarios = [
        (standard, "submit_case", case_payload("claimant"), "standard-claimant-1"),
        (standard, "submit_case", case_payload("claimant"), "standard-claimant-2"),
        (standard, "submit_case", case_payload("respondent"), "standard-respondent"),
        (standard, "submit_case", case_payload("split", 0.55), "standard-split"),
        (inner, "submit_inner_case", case_payload("claimant", 0.2), "inner-claimant"),
        (inner, "submit_inner_case", case_payload("split", 0.65), "inner-split"),
        (appeal, "submit_appeal", appeal_payload(), "appeal-uphold"),
    ]
    results = [execute(client, *scenario) for scenario in scenarios]
    print(json.dumps({"passed": len(results), "results": results}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
