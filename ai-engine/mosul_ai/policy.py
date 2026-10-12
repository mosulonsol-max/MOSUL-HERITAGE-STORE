"""Fail-closed policy checks for autonomous actions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class Decision:
    allowed: bool
    code: str
    reason: str


READ_ONLY = {"research", "capability_audit", "draft_copy"}
REVERSIBLE = {"generate_preview", "queue_social_post"}
FINANCIAL = {"enable_checkout", "settle_auction", "mint_nft", "transfer_token"}


def authorize(action: str, context: Mapping[str, Any] | None = None) -> Decision:
    """Authorize a named capability; unknown or unsafe actions are denied."""
    context = context or {}
    if action in READ_ONLY:
        return Decision(True, "ALLOW_READ_ONLY", "Read-only or draft action.")
    if action in REVERSIBLE:
        if context.get("public_publish") and not context.get("approved_channel"):
            return Decision(False, "DENY_UNAPPROVED_CHANNEL", "Public publishing needs an approved channel.")
        return Decision(True, "ALLOW_REVERSIBLE", "Reversible preview or queue action.")
    if action in FINANCIAL:
        if context.get("network") != "devnet":
            return Decision(False, "DENY_MAINNET", "Financial actions are restricted to Solana devnet.")
        if context.get("real_value"):
            return Decision(False, "DENY_REAL_VALUE", "Real-value transfers are disabled.")
        if not context.get("manual_approval"):
            return Decision(False, "DENY_NO_APPROVAL", "Devnet financial tests require manual approval.")
        return Decision(True, "ALLOW_DEVNET_TEST", "Approved devnet-only test action.")
    return Decision(False, "DENY_UNKNOWN_ACTION", "The action is not in the capability allow-list.")
