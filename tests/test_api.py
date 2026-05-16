import pytest
from fastapi import HTTPException

from apps.api.courter_api.main import health
from apps.api.courter_api.routers.cases import create_case
from apps.api.courter_api.services.courts import CourtConfigurationError, deliberate_case
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
            )
        )

    assert exc.value.status_code == 503
