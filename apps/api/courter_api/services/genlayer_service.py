from __future__ import annotations

import base64
import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any

from ..config import get_settings
from .audit import audit

TX_HASH_RE = re.compile(r"0x[a-fA-F0-9]{64}")

RPC_URLS = {
    "studionet": "https://studio.genlayer.com/api",
    "testnet-bradbury": "https://rpc.bradbury.genlayer.com",
    "testnet-asimov": "https://rpc.asimov.genlayer.com",
}
ROOT = Path(__file__).resolve().parents[4]


def contract_address(court_type: str) -> str | None:
    settings = get_settings()
    return {
        "public": settings.genlayer_standard_court_address,
        "inner": settings.genlayer_inner_court_address,
        "appeal": settings.genlayer_appeal_court_address,
        "shadow_council": settings.genlayer_shadow_council_address,
    }.get(court_type)


def _extract_tx_hash(*values: str) -> str:
    for value in values:
        match = TX_HASH_RE.search(value or "")
        if match:
            return match.group(0)
    return ""


def _rpc_url(network: str) -> str | None:
    return RPC_URLS.get(network)


def _rpc_transaction(tx_hash: str, network: str) -> dict[str, Any] | None:
    rpc_url = _rpc_url(network)
    if not rpc_url:
        return None
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_getTransactionByHash", "params": [tx_hash]})
    try:
        completed = subprocess.run(
            ["curl", "-sS", "-X", "POST", rpc_url, "-H", "content-type: application/json", "--data", payload],
            check=False,
            capture_output=True,
            text=True,
            timeout=45,
        )
        body = json.loads(completed.stdout)
    except (OSError, TimeoutError, json.JSONDecodeError, subprocess.SubprocessError):
        return None
    result = body.get("result")
    return result if isinstance(result, dict) else None


def _json_from_blob(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass
    try:
        raw = base64.b64decode(value + "===")
    except Exception:
        return None
    for start in range(len(raw)):
        if raw[start:start + 1] == b"{":
            candidate = raw[start:]
            try:
                parsed = json.loads(candidate.decode("utf-8", errors="ignore"))
            except json.JSONDecodeError:
                continue
            return parsed if isinstance(parsed, dict) else None
    return None


def extract_contract_judgment(write: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any] | None:
    candidates: list[Any] = []
    candidates.append(write.get("result"))
    rpc = receipt.get("rpc") or {}
    data = rpc.get("data") or {}
    candidates.append(data.get("result"))
    consensus = data.get("consensus_data") or {}
    for item in consensus.get("leader_receipt") or []:
        if isinstance(item, dict):
            candidates.append(item.get("result"))
    for item in consensus.get("validators") or []:
        if isinstance(item, dict):
            candidates.append(item.get("result"))
    for value in candidates:
        parsed = _json_from_blob(value)
        if parsed and "winner" in parsed:
            return parsed
    return None


def write_contract(court_type: str, method: str, payload: dict[str, Any], case_id: str) -> dict[str, Any]:
    settings = get_settings()
    address = contract_address(court_type)
    compact_payload = json.dumps(payload, sort_keys=True)
    if not address:
        missing = {
            "submitted": False,
            "simulated": True,
            "reason": "contract_address_missing",
            "court_type": court_type,
            "method": method,
            "tx_hash": "",
            "status": "NOT_SUBMITTED",
        }
        audit("contract_write_blocked", entity_type="case", entity_id=case_id, severity="critical", metadata=missing)
        return missing

    script_payload = json.dumps({"address": address, "method": method, "payload": compact_payload})
    try:
        completed = subprocess.run(
            ["python3", str(ROOT / "scripts" / "write_studionet_contract.py")],
            input=script_payload,
            check=False,
            capture_output=True,
            text=True,
            timeout=300,
        )
        stdout = completed.stdout
        stderr = completed.stderr
        returncode = completed.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", errors="ignore")
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", errors="ignore")
        returncode = 124
    parsed: dict[str, Any] = {}
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError:
        parsed = {}
    tx_hash = str(parsed.get("tx_hash") or _extract_tx_hash(stdout, stderr))
    result = {
        "submitted": bool(tx_hash) or returncode == 0,
        "simulated": False,
        "address": address,
        "method": method,
        "tx_hash": tx_hash,
        "status": parsed.get("status"),
        "execution_result": parsed.get("execution_result"),
        "result": parsed.get("result"),
        "stdout": stdout,
        "stderr": stderr,
    }
    audit(
        "contract_write_submitted" if result["submitted"] else "contract_write_failed",
        entity_type="case",
        entity_id=case_id,
        severity="info" if result["submitted"] else "critical",
        metadata=result,
    )
    return result


def finalized_receipt(tx_hash: str, case_id: str) -> dict[str, Any]:
    if not tx_hash:
        receipt = {"tx_hash": "", "status": "NOT_SUBMITTED", "simulated": False, "reason": "contract_address_missing"}
        audit("contract_not_finalized", entity_type="case", entity_id=case_id, severity="critical", metadata=receipt)
        return receipt
    if tx_hash.startswith("simulated-"):
        receipt = {"tx_hash": tx_hash, "status": "FINALIZED", "simulated": True}
        audit("contract_finalized", entity_type="case", entity_id=case_id, metadata=receipt)
        return receipt
    settings = get_settings()
    rpc_result: dict[str, Any] | None = None
    for _ in range(12):
        rpc_result = _rpc_transaction(tx_hash, settings.genlayer_contract_network)
        if rpc_result and rpc_result.get("status") == "FINALIZED":
            break
        time.sleep(5)

    execution_result = ((rpc_result or {}).get("data") or {}).get("execution_result")
    rpc_stderr = ((rpc_result or {}).get("data") or {}).get("stderr")
    result_name = ((rpc_result or {}).get("data") or {}).get("result_name")
    leader_receipt = (((rpc_result or {}).get("data") or {}).get("consensus_data") or {}).get("leader_receipt") or []
    leader_error = any((item.get("genvm_result") or {}).get("execution_result") == "ERROR" for item in leader_receipt if isinstance(item, dict))
    finalized = (
        (rpc_result or {}).get("status") == "FINALIZED"
        and execution_result != "ERROR"
        and result_name != "NO_MAJORITY"
        and not leader_error
    )
    receipt = {
        "tx_hash": tx_hash,
        "status": "FINALIZED" if finalized else "ERROR",
        "stdout": "",
        "stderr": rpc_stderr or "",
        "rpc": rpc_result,
    }
    audit("contract_finalized" if finalized else "contract_failed", entity_type="case", entity_id=case_id, severity="info" if finalized else "critical", metadata=receipt)
    return receipt
