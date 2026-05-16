from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from decimal import Decimal

from courter_shared.constants import COURT_FEES_GEN

from ..config import get_settings
from .audit import audit
from .repository import repo


@dataclass(frozen=True)
class PaymentVerification:
    ok: bool
    public_message: str
    internal_reason: str
    receipt: dict
    payment: dict | None = None


def _development_receipt(tx_hash: str, sender_wallet: str, recipient_wallet: str, amount_gen: Decimal) -> dict:
    return {
        "tx_hash": tx_hash,
        "sender": sender_wallet,
        "recipient": recipient_wallet,
        "amount_gen": str(amount_gen),
        "status": "0x1",
        "source": "development-adapter",
        "rpc_url": "development",
        "fallback_used": False,
        "tx_found": True,
        "receipt_found": True,
    }


def _payment_message(reason: str) -> str:
    messages = {
        "malformed_tx_hash": "Enter a valid transaction hash.",
        "replayed_tx_hash": "This transaction has already been used.",
        "unknown_court_type": "This court type is not configured for payment verification.",
        "wrong_payment_amount": "The submitted payment amount does not match the required court fee.",
        "malformed_sender_wallet": "Enter the sender wallet that paid on Bradbury.",
        "transaction_not_found": "This transaction could not be found on Bradbury.",
        "transaction_pending": "This transaction exists on Bradbury but has not been processed yet.",
        "transaction_failed": "This Bradbury transaction failed and cannot be used for payment verification.",
        "sender_wallet_mismatch": "The sender wallet does not match the wallet that paid on Bradbury.",
        "treasury_wallet_mismatch": "The payment was not sent to the Courter treasury wallet.",
        "receipt_amount_missing": "The payment amount could not be read from Bradbury.",
        "receipt_amount_mismatch": "The payment amount on Bradbury does not match the required court fee.",
    }
    return messages.get(reason, "Payment verification failed on Bradbury.")


def _normalize_rpc_url(url: str) -> str:
    normalized = (url or "").strip()
    if normalized.startswith("http://"):
        return f"https://{normalized.removeprefix('http://')}"
    return normalized


def _rpc_call(rpc_url: str, method: str, params: list[object]) -> dict:
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
    try:
        completed = subprocess.run(
            ["curl", "-L", "-sS", "-X", "POST", rpc_url, "-H", "content-type: application/json", "--data", payload],
            check=False,
            capture_output=True,
            text=True,
            timeout=45,
        )
    except Exception as exc:
        return {"ok": False, "error": str(exc), "rpc_url": rpc_url, "method": method}
    if completed.returncode != 0:
        return {"ok": False, "error": completed.stderr.strip() or completed.stdout.strip(), "rpc_url": rpc_url, "method": method}
    try:
        body = json.loads(completed.stdout or "{}")
    except json.JSONDecodeError:
        return {"ok": False, "error": "invalid_json", "stdout": completed.stdout.strip(), "rpc_url": rpc_url, "method": method}
    if body.get("error"):
        return {"ok": False, "error": body["error"], "rpc_url": rpc_url, "method": method, "body": body}
    return {"ok": True, "result": body.get("result"), "rpc_url": rpc_url, "method": method}


def _resolve_bradbury_receipt(tx_hash: str) -> dict:
    settings = get_settings()
    urls = [
        _normalize_rpc_url(settings.bradbury_payment_rpc_primary),
        _normalize_rpc_url(settings.bradbury_payment_rpc_fallback),
    ]
    tried: list[dict] = []
    for index, rpc_url in enumerate(urls):
        if not rpc_url:
            continue
        tx_result = _rpc_call(rpc_url, "eth_getTransactionByHash", [tx_hash])
        tried.append(tx_result)
        if not tx_result.get("ok"):
            continue
        tx = tx_result.get("result")
        if not isinstance(tx, dict) or not tx:
            continue
        receipt_result = _rpc_call(rpc_url, "eth_getTransactionReceipt", [tx_hash])
        tried.append(receipt_result)
        receipt = receipt_result.get("result") if receipt_result.get("ok") else None
        return {
            "status": (receipt or {}).get("status"),
            "source": "bradbury-rpc",
            "rpc_url": rpc_url,
            "fallback_used": index > 0,
            "tx_found": True,
            "receipt_found": isinstance(receipt, dict),
            "tx": tx,
            "rpc_receipt": receipt if isinstance(receipt, dict) else None,
            "tried": tried,
        }
    return {
        "status": None,
        "source": "bradbury-rpc",
        "rpc_url": urls[0] if urls else "",
        "fallback_used": len(urls) > 1,
        "tx_found": False,
        "receipt_found": False,
        "tx": None,
        "rpc_receipt": None,
        "tried": tried,
    }


def payment_rpc_health() -> dict[str, object]:
    settings = get_settings()
    checks = []
    for label, raw_url in (
        ("primary", settings.bradbury_payment_rpc_primary),
        ("fallback", settings.bradbury_payment_rpc_fallback),
    ):
        rpc_url = _normalize_rpc_url(raw_url)
        result = _rpc_call(rpc_url, "eth_blockNumber", [])
        status = "healthy" if result.get("ok") and result.get("result") else "down"
        checks.append(
            {
                "name": label,
                "rpc_url": rpc_url,
                "status": status,
                "block_number": result.get("result"),
                "error": result.get("error"),
            }
        )
    overall = "healthy" if any(item["status"] == "healthy" for item in checks) else "down"
    return {"status": overall, "checks": checks}


def _receipt_sender(receipt: dict) -> str:
    tx = receipt.get("tx") or {}
    rpc_receipt = receipt.get("rpc_receipt") or {}
    return str(
        receipt.get("sender")
        or tx.get("from")
        or rpc_receipt.get("from")
        or receipt.get("from")
        or receipt.get("from_address")
        or ((receipt.get("rpc") or {}).get("from_address"))
        or ""
    )


def _receipt_recipient(receipt: dict) -> str:
    tx = receipt.get("tx") or {}
    rpc_receipt = receipt.get("rpc_receipt") or {}
    return str(
        receipt.get("recipient")
        or tx.get("to")
        or rpc_receipt.get("to")
        or receipt.get("to")
        or receipt.get("to_address")
        or ((receipt.get("rpc") or {}).get("to_address"))
        or ""
    )


def _receipt_amount_gen(receipt: dict) -> Decimal | None:
    tx = receipt.get("tx") or {}
    candidates = [
        receipt.get("amount_gen"),
        receipt.get("amount"),
        tx.get("value"),
        receipt.get("value"),
        (receipt.get("rpc") or {}).get("value"),
    ]
    for value in candidates:
        if value is None or value == "":
            continue
        try:
            if isinstance(value, str) and value.startswith("0x"):
                return Decimal(int(value, 16)) / Decimal(10**18)
            return Decimal(str(value))
        except Exception:
            continue
    return None


def verify_payment(
    *,
    tx_hash: str,
    sender_wallet: str,
    recipient_wallet: str,
    amount_gen: int | float | Decimal,
    court_type: str,
    finalized: bool = True,
    actor_id: str = "anonymous",
    consume: bool = False,
) -> PaymentVerification:
    del finalized
    settings = get_settings()
    expected_amount = Decimal(str(COURT_FEES_GEN.get(court_type, -1)))
    submitted_amount = Decimal(str(amount_gen))
    receipt = (
        _development_receipt(tx_hash, sender_wallet, recipient_wallet, submitted_amount)
        if settings.payment_verification_mode == "development"
        else _resolve_bradbury_receipt(tx_hash)
    )
    reason = ""
    receipt_sender = _receipt_sender(receipt)
    receipt_recipient = _receipt_recipient(receipt)
    receipt_amount = _receipt_amount_gen(receipt)
    receipt_status = str(receipt.get("status") or "").lower()

    if not tx_hash.startswith("0x") or len(tx_hash) < 10:
        reason = "malformed_tx_hash"
    elif repo.payment_consumed(tx_hash):
        reason = "replayed_tx_hash"
    elif expected_amount < 0:
        reason = "unknown_court_type"
    elif submitted_amount != expected_amount:
        reason = "wrong_payment_amount"
    elif not sender_wallet.startswith("0x"):
        reason = "malformed_sender_wallet"
    elif settings.payment_verification_mode != "development" and not receipt.get("tx_found"):
        reason = "transaction_not_found"
    elif settings.payment_verification_mode != "development" and not receipt.get("receipt_found"):
        reason = "transaction_pending"
    elif settings.payment_verification_mode != "development" and receipt_status != "0x1":
        reason = "transaction_failed"
    elif recipient_wallet.lower() != settings.treasury_wallet.lower():
        reason = "treasury_wallet_mismatch"
    elif settings.payment_verification_mode != "development" and receipt_sender.lower() != sender_wallet.lower():
        reason = "sender_wallet_mismatch"
    elif settings.payment_verification_mode != "development" and receipt_recipient.lower() != settings.treasury_wallet.lower():
        reason = "treasury_wallet_mismatch"
    elif settings.payment_verification_mode != "development" and receipt_amount is None:
        reason = "receipt_amount_missing"
    elif settings.payment_verification_mode != "development" and receipt_amount != expected_amount:
        reason = "receipt_amount_mismatch"

    if reason:
        audit(
            "payment_failed",
            actor_type="user",
            actor_id=actor_id,
            entity_type="payment",
            entity_id=tx_hash,
            severity="warning",
            metadata={"reason": reason, "court_type": court_type, "receipt": receipt},
        )
        return PaymentVerification(False, _payment_message(reason), reason, receipt, None)

    payment = {
        "tx_hash": tx_hash,
        "sender_wallet": sender_wallet,
        "recipient_wallet": recipient_wallet,
        "court_type": court_type,
        "amount_gen": float(submitted_amount),
        "receipt_sender": receipt_sender,
        "receipt_recipient": receipt_recipient,
        "receipt_amount_gen": float(receipt_amount) if receipt_amount is not None else None,
        "receipt": receipt,
    }
    if consume:
        repo.consume_payment(payment)
        audit(
            "payment_verified",
            actor_type="user",
            actor_id=actor_id,
            entity_type="payment",
            entity_id=tx_hash,
            metadata=payment,
        )
        return PaymentVerification(True, "Payment verified. The treasury has received the required GEN.", "payment_verified", receipt, payment)

    audit(
        "payment_checked",
        actor_type="user",
        actor_id=actor_id,
        entity_type="payment",
        entity_id=tx_hash,
        metadata=payment,
    )
    return PaymentVerification(
        True,
        f"{expected_amount} GEN has been received in the treasury. You can proceed to submit your case.",
        "payment_checked",
        receipt,
        payment,
    )


def consume_verified_payment(*, payment: dict, actor_id: str = "anonymous") -> PaymentVerification:
    tx_hash = str(payment["tx_hash"])
    if repo.payment_consumed(tx_hash):
        audit(
            "payment_failed",
            actor_type="user",
            actor_id=actor_id,
            entity_type="payment",
            entity_id=tx_hash,
            severity="warning",
            metadata={"reason": "replayed_tx_hash", "court_type": payment.get("court_type"), "receipt": payment.get("receipt", {})},
        )
        return PaymentVerification(False, _payment_message("replayed_tx_hash"), "replayed_tx_hash", payment.get("receipt", {}), None)

    repo.consume_payment(payment)
    audit(
        "payment_verified",
        actor_type="user",
        actor_id=actor_id,
        entity_type="payment",
        entity_id=tx_hash,
        metadata=payment,
    )
    return PaymentVerification(True, "Payment verified. The treasury has received the required GEN.", "payment_verified", payment.get("receipt", {}), payment)
