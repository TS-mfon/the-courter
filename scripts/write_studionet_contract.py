from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from eth_account import Account
from genlayer_py.chains.studionet import studionet
from genlayer_py.client import create_client

from deploy_studionet_contracts import patch_web3_contract_fn_compat, wait_finalized


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    load_dotenv(ROOT / ".env.test")
    request = json.loads(sys.stdin.read())
    patch_web3_contract_fn_compat()
    client = create_client(chain=studionet, account=Account.from_key(os.environ["GENLAYER_PRIVATE_KEY"]))
    tx_hash = client.write_contract(
        address=request["address"],
        function_name=request["method"],
        args=[request["payload"]],
    )
    receipt = wait_finalized(tx_hash)
    data = receipt.get("data") or {}
    print(
        json.dumps(
            {
                "submitted": True,
                "simulated": False,
                "address": request["address"],
                "method": request["method"],
                "tx_hash": tx_hash,
                "status": receipt.get("status"),
                "execution_result": data.get("execution_result"),
                "stdout": data.get("stdout") or "",
                "stderr": data.get("stderr") or "",
                "result": data.get("result"),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
