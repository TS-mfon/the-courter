from apps.api.courter_api.config import get_settings
from apps.api.courter_api.services.payments import verify_payment
from apps.api.courter_api.services.repository import repo
from courter_shared.constants import TREASURY_WALLET


def setup_function() -> None:
    get_settings().payment_verification_mode = "development"
    repo.payments.clear()
    repo.audit_logs.clear()


def test_valid_payment_consumes_tx() -> None:
    result = verify_payment(
        tx_hash="0xvalidpayment001",
        sender_wallet="0xabc",
        recipient_wallet=TREASURY_WALLET,
        amount_gen=2,
        court_type="public",
    )
    assert result.ok is True
    assert repo.payment_consumed("0xvalidpayment001")


def test_reused_tx_gets_warning_and_private_log() -> None:
    verify_payment(
        tx_hash="0xvalidpayment002",
        sender_wallet="0xabc",
        recipient_wallet=TREASURY_WALLET,
        amount_gen=2,
        court_type="public",
    )
    result = verify_payment(
        tx_hash="0xvalidpayment002",
        sender_wallet="0xabc",
        recipient_wallet=TREASURY_WALLET,
        amount_gen=2,
        court_type="public",
    )
    assert result.ok is False
    assert result.public_message == "This transaction has already been used."
    assert result.internal_reason == "replayed_tx_hash"


def test_wrong_amount_gets_warning() -> None:
    result = verify_payment(
        tx_hash="0xunderpaid001",
        sender_wallet="0xabc",
        recipient_wallet=TREASURY_WALLET,
        amount_gen=1,
        court_type="public",
    )
    assert result.ok is False
    assert result.public_message == "The submitted payment amount does not match the required court fee."
    assert repo.audit_logs[-1]["metadata"]["reason"] == "wrong_payment_amount"
