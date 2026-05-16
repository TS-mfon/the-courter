from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

import eth_utils
from eth_abi import encode as abi_encode
from dotenv import load_dotenv
from eth_account import Account
from genlayer_py.chains.studionet import studionet
from genlayer_py.client import create_client
import genlayer_py.contracts.actions as contract_actions
from genlayer_py.exceptions import GenLayerError
from web3.logs import DISCARD


ROOT = Path(__file__).resolve().parents[1]
RPC_URL = "https://studio.genlayer.com/api"
CONTRACTS = [
    ("standard", "GENLAYER_STANDARD_COURT_ADDRESS", "contracts/standard_court.py"),
    ("inner", "GENLAYER_INNER_COURT_ADDRESS", "contracts/inner_court.py"),
    ("appeal", "GENLAYER_APPEAL_COURT_ADDRESS", "contracts/appeal_court.py"),
    ("shadow", "GENLAYER_SHADOW_COUNCIL_ADDRESS", "contracts/shadow_council.py"),
]


def patch_web3_contract_fn_compat() -> None:
    def encode_add_transaction_data(self, sender_account, recipient, consensus_max_rotations, data, valid_until=0):
        consensus_main_contract = self.w3.eth.contract(abi=self.chain.consensus_main_contract["abi"])
        contract_fn = consensus_main_contract.get_function_by_name("addTransaction")
        argument_types = getattr(contract_fn, "argument_types", None)
        if argument_types is None:
            argument_types = [item["type"] for item in contract_fn.abi["inputs"]]
        add_transaction_args = [
            sender_account.address,
            recipient,
            self.chain.default_number_of_initial_validators,
            consensus_max_rotations,
            self.w3.to_bytes(hexstr=data),
        ]
        if len(argument_types) >= 6:
            add_transaction_args.append(valid_until)
        params = abi_encode(argument_types, add_transaction_args)
        signature = getattr(contract_fn, "signature", None)
        if signature is None:
            signature = f"{contract_fn.fn_name}({','.join(argument_types)})"
        function_selector = eth_utils.keccak(text=signature)[:4].hex()
        return "0x" + function_selector + params.hex()

    contract_actions._encode_add_transaction_data = encode_add_transaction_data

    def send_transaction(self, encoded_data, sender_account=None, value=0, sim_config=None):
        if sender_account is None:
            raise GenLayerError("No account set.")
        transaction = contract_actions._prepare_transaction(
            self=self,
            sender=sender_account.address,
            recipient=self.chain.consensus_main_contract["address"],
            data=encoded_data,
            value=value,
        )
        signed_transaction = sender_account.sign_transaction(transaction)
        serialized_transaction = self.w3.to_hex(signed_transaction.raw_transaction)
        params = [serialized_transaction]
        if sim_config is not None:
            params.append(sim_config)
        raw_tx_hash = self.provider.make_request(method="eth_sendRawTransaction", params=params)["result"]
        if os.environ.get("COURTER_DEPLOY_VERBOSE") == "1":
            print(json.dumps({"raw_tx_hash": raw_tx_hash, "status": "raw_submitted"}, sort_keys=True), flush=True)
        raw_receipt = None
        for _ in range(60):
            raw_receipt = rpc("eth_getTransactionReceipt", [raw_tx_hash]).get("result")
            if raw_receipt:
                break
            time.sleep(2)
        if not raw_receipt:
            raise GenLayerError(f"Raw transaction receipt timed out: {raw_tx_hash}")
        if raw_receipt.get("status") not in ("0x1", 1):
            raise GenLayerError(f"Raw transaction failed: {raw_tx_hash}")
        consensus_main_contract = self.w3.eth.contract(abi=self.chain.consensus_main_contract["abi"])
        event = consensus_main_contract.get_event_by_name("NewTransaction")
        events = event.process_receipt(raw_receipt, DISCARD)
        if len(events) == 0:
            raise GenLayerError("Transaction not processed by consensus")
        return self.w3.to_hex(events[0]["args"]["txId"])

    contract_actions._send_transaction = send_transaction


def rpc(method: str, params: list) -> dict:
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
    completed = subprocess.run(
        ["curl", "-sS", "-X", "POST", RPC_URL, "-H", "content-type: application/json", "--data", payload],
        check=True,
        capture_output=True,
        text=True,
        timeout=45,
    )
    return json.loads(completed.stdout)


def wait_finalized(tx_hash: str) -> dict:
    for _ in range(30):
        result = rpc("eth_getTransactionByHash", [tx_hash]).get("result")
        if result and result.get("status") == "FINALIZED":
            return result
        time.sleep(4)
    raise RuntimeError(f"Timed out waiting for {tx_hash}")


def deployed_address(receipt: dict) -> str:
    data = receipt.get("data") or {}
    if data.get("execution_result") == "ERROR":
        stderr = data.get("stderr") or "unknown GenVM error"
        raise RuntimeError(stderr)
    address = data.get("contract_address") or (data.get("contract_snapshot") or {}).get("contract_address")
    if not address:
        raise RuntimeError("Deployment finalized without a contract address")
    schema = rpc("gen_getContractSchema", [address])
    if schema.get("error"):
        raise RuntimeError(json.dumps(schema["error"], sort_keys=True))
    return address


def main() -> None:
    load_dotenv(ROOT / ".env.test")
    os.environ["COURTER_DEPLOY_VERBOSE"] = "1"
    patch_web3_contract_fn_compat()
    private_key = os.environ["GENLAYER_PRIVATE_KEY"]
    client = create_client(chain=studionet, account=Account.from_key(private_key))
    results = {}
    for name, env_key, relative_path in CONTRACTS:
        code = (ROOT / relative_path).read_text(encoding="utf-8")
        tx_hash = client.deploy_contract(code=code, args=[])
        print(json.dumps({"name": name, "tx_hash": tx_hash, "status": "submitted"}, sort_keys=True), flush=True)
        receipt = wait_finalized(tx_hash)
        address = deployed_address(receipt)
        results[env_key] = {"name": name, "address": address, "tx_hash": tx_hash}
        print(json.dumps(results[env_key], sort_keys=True), flush=True)
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
