import pytest
from fastapi import HTTPException

from apps.api.courter_api.main import health
from apps.api.courter_api.routers.cases import create_case
from apps.api.courter_api.services.courts import CourtConfigurationError, deliberate_case, refresh_case_finalization
from courter_shared.schemas import CaseIntake
from courter_shared.schemas import ContradictionReport, StructuredEvidence


def test_health() -> None:
    assert health()["status"] == "ok"


def test_case_flow_returns_finalized_verdict() -> None:
    body = create_case(
        CaseIntake(
            username="ada",
            country="nigeria",
            dispute_type="land",
            court_type="public",
            claimant_statement="I hold the land certificate REG-291 signed in 2021 with ownership transfer records, payment receipt, and registry confirmation from the land office.",
            agreement_confirmed=True,
        )
    )
    assert body["status"] in {"finalized", "awaiting_genlayer_contract"}
    assert "genlayer" not in body
    assert "admin_diagnostics" not in body
    assert "verdict" in body
    assert "judge_panels" in body["verdict"]


def test_vague_case_rejected_before_verdict() -> None:
    with pytest.raises(HTTPException):
        create_case(
            CaseIntake(
                username="ada",
                country="nigeria",
                dispute_type="land",
                court_type="public",
                claimant_statement="testing testing testing",
            )
        )


def test_criminal_case_rejected() -> None:
    with pytest.raises(HTTPException):
        create_case(
            CaseIntake(
                username="ada",
                country="nigeria",
                dispute_type="criminal",
                court_type="public",
                claimant_statement="This is a criminal accusation.",
            )
        )


def test_deliberate_case_rejects_empty_judge_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("apps.api.courter_api.services.courts.select_judges", lambda **_: [])

    with pytest.raises(CourtConfigurationError):
        deliberate_case(
            CaseIntake(
                username="ada",
                country="nigeria",
                dispute_type="land",
                court_type="public",
                claimant_statement="I hold the land certificate REG-291 signed in 2021 with ownership transfer records.",
            ),
            [StructuredEvidence(document_type="land_certificate", country="Nigeria", confidence=0.91)],
            ContradictionReport(contradiction_detected=False, severity=0, issues=[]),
            [{"section_id": "NIG-LAN-001", "title": "Ownership", "summary": "Summary", "importance": 0.9}],
        )


def test_case_flow_returns_controlled_error_when_judge_registry_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("apps.api.courter_api.services.courts.select_judges", lambda **_: [])

    with pytest.raises(HTTPException) as exc:
        create_case(
            CaseIntake(
                username="ada",
                country="nigeria",
                dispute_type="land",
                court_type="public",
                claimant_statement="I hold the land certificate REG-291 signed in 2021 with ownership transfer records, registry confirmation from the land office, payment receipt, witness statements, and survey plan references for Plot 14.",
                agreement_confirmed=True,
            )
        )

    assert exc.value.status_code == 503


def test_pending_case_keeps_draft_winner_visible(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("apps.api.courter_api.services.courts.write_contract", lambda *args, **kwargs: {
        "submitted": True,
        "simulated": False,
        "address": "0xabc",
        "method": "submit_case",
        "tx_hash": "0x" + "1" * 64,
        "status": None,
        "execution_result": None,
        "result": None,
        "stdout": "",
        "stderr": "",
    })
    monkeypatch.setattr("apps.api.courter_api.services.courts.finalized_receipt", lambda *args, **kwargs: {
        "tx_hash": "0x" + "1" * 64,
        "status": "ERROR",
        "stdout": "",
        "stderr": "",
        "rpc": None,
    })

    body = create_case(
        CaseIntake(
            username="ada",
            country="nigeria",
            dispute_type="land",
            court_type="public",
            claimant_statement="I hold the land certificate REG-291 signed in 2021 with ownership transfer records, payment receipt, and registry confirmation from the land office.",
            agreement_confirmed=True,
        )
    )

    assert body["status"] == "awaiting_genlayer_contract"
    assert body["verdict"]["winner"] == "claimant"
    assert body["plain_english_verdict"] == body["verdict"]["headline_verdict"]
    assert body["verdict"]["reasoning_summary"][0].startswith("The contract was triggered on submission")


def test_refresh_case_finalization_resubmits_when_missing_tx(monkeypatch: pytest.MonkeyPatch) -> None:
    record = {
        "id": "CASE-TEST1234",
        "username": "ada",
        "country": "nigeria",
        "dispute_type": "land",
        "court_type": "public",
        "status": "awaiting_genlayer_contract",
        "public": True,
        "created_at": "2026-05-16T00:00:00Z",
        "updated_at": "2026-05-16T00:00:00Z",
        "input": CaseIntake(
            username="ada",
            country="nigeria",
            dispute_type="land",
            court_type="public",
            claimant_statement="I hold title REG-291 with survey plan and registry confirmation.",
        ).model_dump(),
        "structured_evidence": [StructuredEvidence(document_type="land_certificate", country="nigeria", registry_id="REG-291", confidence=0.86).model_dump()],
        "contradiction_report": {"contradiction_detected": False, "severity": 0.0, "issues": []},
        "timeline": [],
        "fraud_report": {"suspicious": False, "signals": [], "severity": 0.0},
        "retrieved_laws": [{"section_id": "NIG-LAN-001", "title": "Ownership", "summary": "Summary", "importance": 0.9}],
        "judge_reasoning": [],
        "verdict": {
            "winner": "claimant",
            "confidence": 0.84,
            "judges_used": ["Justice Ratio"],
            "laws_used": ["NIG-LAN-001"],
            "reasoning_summary": [],
            "contradictions": [],
            "headline_verdict": "The claimant has the stronger civil position.",
            "final_conclusion": "Draft conclusion.",
            "filing_summary": "Land Certificate",
            "evidence_overview": "1 structured evidence item",
            "judge_panels": [],
            "law_citations": [],
            "appealable": True,
            "finalized": False,
        },
        "plain_english_verdict": "The claimant has the stronger civil position.",
        "admin_diagnostics": {"genlayer": {"write": {"submitted": False, "tx_hash": ""}}, "route_to_complex_analysis": False},
    }
    saved: dict = {}

    monkeypatch.setattr("apps.api.courter_api.services.courts.load_judge_profiles", lambda: [{"name": "Justice Ratio"}])
    monkeypatch.setattr("apps.api.courter_api.services.courts.write_contract", lambda *args, **kwargs: {
        "submitted": True,
        "simulated": False,
        "address": "0xabc",
        "method": "submit_case",
        "tx_hash": "0x" + "2" * 64,
        "status": None,
        "execution_result": None,
        "result": None,
        "stdout": "",
        "stderr": "",
    })
    monkeypatch.setattr("apps.api.courter_api.services.courts.finalized_receipt", lambda *args, **kwargs: {
        "tx_hash": "0x" + "2" * 64,
        "status": "ERROR",
        "stdout": "",
        "stderr": "",
        "rpc": None,
    })
    monkeypatch.setattr("apps.api.courter_api.services.courts.repo.save_case", lambda value: saved.update(value) or value)

    refreshed = refresh_case_finalization(record)

    assert refreshed["admin_diagnostics"]["genlayer"]["write"]["tx_hash"] == "0x" + "2" * 64
    assert refreshed["verdict"]["winner"] == "claimant"
    assert saved["admin_diagnostics"]["genlayer"]["write"]["tx_hash"] == "0x" + "2" * 64
