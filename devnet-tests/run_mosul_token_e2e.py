#!/usr/bin/env python3
"""Devnet-only Token-2022 payment rehearsal with throwaway wallets and mint.

The script creates a fresh six-decimal test mint. It never reads a keypair from
disk and never references the project's Mainnet MOSUL mint.
"""
from __future__ import annotations

import asyncio
import json
import tempfile
from pathlib import Path

from solana.rpc.async_api import AsyncClient
from solders.instruction import Instruction
from solders.keypair import Keypair
from solders.message import MessageV0
from solders.pubkey import Pubkey
from solders.system_program import CreateAccountParams, create_account
from solders.transaction import VersionedTransaction
from spl.token.constants import ASSOCIATED_TOKEN_PROGRAM_ID, TOKEN_2022_PROGRAM_ID
from spl.token.models import (
    InitializeMintParams,
    MintToCheckedParams,
    TransferCheckedParams,
)
from spl.token.instructions import (
    create_associated_token_account,
    initialize_mint,
    mint_to_checked,
    transfer_checked,
)

from core import (DevnetRpc, claim_refund, comparable_sales, confirm_payment,
                  connect, create_intent, finalize_refund, request_refund)

RPC = "https://api.devnet.solana.com"
MEMO_PROGRAM = Pubkey.from_string("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr")
DECIMALS = 6
PAYMENT_RAW = 125_000_000


async def send(client: AsyncClient, payer: Keypair, instructions: list[Instruction],
               extra_signers: list[Keypair] | None = None) -> str:
    blockhash = (await client.get_latest_blockhash()).value.blockhash
    message = MessageV0.try_compile(payer.pubkey(), instructions, [], blockhash)
    transaction = VersionedTransaction(message, [payer, *(extra_signers or [])])
    signature = (await client.send_transaction(transaction)).value
    await client.confirm_transaction(signature, commitment="finalized")
    return str(signature)


async def fund(client: AsyncClient, wallet: Pubkey) -> None:
    for attempt in range(3):
        try:
            signature = (await client.request_airdrop(wallet, 100_000_000)).value
            await client.confirm_transaction(signature, commitment="finalized")
            return
        except Exception:
            if attempt == 2:
                raise RuntimeError("Devnet faucet/RPC unavailable; no sale or payment was made") from None
            await asyncio.sleep(4 * (attempt + 1))


async def run() -> int:
    client = AsyncClient(RPC)
    payer, merchant, mint = Keypair(), Keypair(), Keypair()
    buyer = payer
    try:
        await fund(client, payer.pubkey())
        mint_rent = (await client.get_minimum_balance_for_rent_exemption(82)).value
        await send(client, payer, [
            create_account(CreateAccountParams(
                from_pubkey=payer.pubkey(), to_pubkey=mint.pubkey(), lamports=mint_rent,
                space=82, owner=TOKEN_2022_PROGRAM_ID,
            )),
            initialize_mint(InitializeMintParams(
                decimals=DECIMALS, program_id=TOKEN_2022_PROGRAM_ID, mint=mint.pubkey(),
                mint_authority=payer.pubkey(), freeze_authority=None,
            )),
        ], [mint])

        buyer_ata = Pubkey.find_program_address(
            [bytes(buyer.pubkey()), bytes(TOKEN_2022_PROGRAM_ID), bytes(mint.pubkey())],
            ASSOCIATED_TOKEN_PROGRAM_ID,
        )[0]
        merchant_ata = Pubkey.find_program_address(
            [bytes(merchant.pubkey()), bytes(TOKEN_2022_PROGRAM_ID), bytes(mint.pubkey())],
            ASSOCIATED_TOKEN_PROGRAM_ID,
        )[0]
        await send(client, payer, [
            create_associated_token_account(payer.pubkey(), buyer.pubkey(), mint.pubkey(), TOKEN_2022_PROGRAM_ID),
            create_associated_token_account(payer.pubkey(), merchant.pubkey(), mint.pubkey(), TOKEN_2022_PROGRAM_ID),
        ])
        await send(client, payer, [mint_to_checked(MintToCheckedParams(
            program_id=TOKEN_2022_PROGRAM_ID, mint=mint.pubkey(), dest=buyer_ata,
            mint_authority=payer.pubkey(), amount=PAYMENT_RAW, decimals=DECIMALS,
        ))])

        with tempfile.TemporaryDirectory(prefix="mosul-devnet-payment-") as folder:
            db = connect(Path(folder) / "payments.sqlite3")
            intent = create_intent(
                db, idempotency_key="live-devnet-token-2022-e2e", item_id="test-preview",
                category="devnet-nft-test", amount_lamports=PAYMENT_RAW, price_usd="1.25",
                merchant=str(merchant.pubkey()), buyer=str(buyer.pubkey()),
                asset_mint=str(mint.pubkey()), asset_decimals=DECIMALS,
            )
            signature = await send(client, buyer, [
                transfer_checked(TransferCheckedParams(
                    program_id=TOKEN_2022_PROGRAM_ID, source=buyer_ata, mint=mint.pubkey(),
                    dest=merchant_ata, owner=buyer.pubkey(), amount=PAYMENT_RAW, decimals=DECIMALS,
                )),
                Instruction(MEMO_PROGRAM, intent["memo"].encode("utf-8"), []),
            ])
            confirmed = confirm_payment(db, intent["id"], signature, DevnetRpc())
            request_refund(db, intent["id"], intent["refund_token"])
            claim_refund(db, intent["id"])
            refund_signature = await send(client, buyer, [
                transfer_checked(TransferCheckedParams(
                    program_id=TOKEN_2022_PROGRAM_ID, source=merchant_ata, mint=mint.pubkey(),
                    dest=buyer_ata, owner=merchant.pubkey(), amount=PAYMENT_RAW, decimals=DECIMALS,
                )),
                Instruction(MEMO_PROGRAM, ("REFUND:" + intent["id"]).encode("utf-8"), []),
            ], [merchant])
            refunded = finalize_refund(db, intent["id"], refund_signature, DevnetRpc())
            print(json.dumps({
                "network": "devnet", "asset": "ephemeral Token-2022 test mint",
                "mint": str(mint.pubkey()), "decimals": DECIMALS,
                "amount_base_units": PAYMENT_RAW, "payment_status": confirmed["status"],
                "payment_signature": signature,
                "refund_status": refunded["status"], "refund_signature": refund_signature,
                "comparables_after_refund": len(comparable_sales(db)["comparables"]),
                "explorer": f"https://solscan.io/tx/{signature}?cluster=devnet",
                "private_keys_persisted": False,
            }, indent=2))
        return 0
    finally:
        await client.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
