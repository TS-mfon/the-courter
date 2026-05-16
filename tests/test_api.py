import pytest
from fastapi import HTTPException

from apps.api.courter_api.main import health
from apps.api.courter_api.routers.cases import create_case
from courter_shared.schemas import CaseIntake


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
