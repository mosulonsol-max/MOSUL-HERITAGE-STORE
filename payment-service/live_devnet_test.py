#!/usr/bin/env python3
"""One-shot live Devnet rehearsal using ephemeral keys; no keys are persisted."""
from __future__ import annotations

import json
import asyncio
import tempfile
import time
from pathlib import Path

from solana.rpc.async_api import AsyncClient
from solders.instruction import Instruction
from solders.keypair import Keypair
from solders.message import MessageV0
from solders.pubkey import Pubkey
from solders.system_program import TransferParams, transfer
from solders.transaction import VersionedTransaction

from core import DevnetRpc, comparable_sales, confirm_payment, connect, create_intent

RPC = "https://api.devnet.solana.com"
MEMO_PROGRAM = Pubkey.from_string("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr")


async def run() -> int:
    client = AsyncClient(RPC)
    buyer, merchant = Keypair(), Keypair()
    airdrop = None
    for attempt in range(3):
        try:
            airdrop = (await client.request_airdrop(buyer.pubkey(), 20_000_000)).value
            break
        except Exception:
            if attempt == 2:
                await client.close()
                raise RuntimeError("Devnet faucet refused the airdrop; retry later or fund the ephemeral test wallet from an approved faucet") from None
            await asyncio.sleep(3 * (attempt + 1))
    await client.confirm_transaction(airdrop, commitment="finalized")
    with tempfile.TemporaryDirectory() as folder:
        db = connect(Path(folder) / "payments.sqlite3")
        intent = create_intent(db, idempotency_key="live-devnet-rehearsal", item_id="test-preview",
            category="digital-art-one-of-one", amount_lamports=1_000_000, price_usd="1",
            merchant=str(merchant.pubkey()), buyer=str(buyer.pubkey()))
        blockhash = (await client.get_latest_blockhash()).value.blockhash
        instructions = [
            transfer(TransferParams(from_pubkey=buyer.pubkey(), to_pubkey=merchant.pubkey(), lamports=1_000_000)),
            Instruction(MEMO_PROGRAM, intent["memo"].encode("utf-8"), []),
        ]
        message = MessageV0.try_compile(buyer.pubkey(), instructions, [], blockhash)
        transaction = VersionedTransaction(message, [buyer])
        signature = (await client.send_transaction(transaction)).value
        await client.confirm_transaction(signature, commitment="finalized")
        result = confirm_payment(db, intent["id"], str(signature), DevnetRpc())
        sales = comparable_sales(db)["comparables"]
    print(json.dumps({
        "network": "devnet", "payment_status": result["status"], "signature": str(signature),
        "ledger_rows": len(sales), "explorer": f"https://solscan.io/tx/{signature}?cluster=devnet"
    }, indent=2))
    await client.close()
    return 0


def main() -> int:
    return asyncio.run(run())


if __name__ == "__main__":
    raise SystemExit(main())
