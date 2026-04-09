"""
Discord webhook notification module for DropAgent.

Sends alerts, digest summaries, and margin results to a Discord channel
via a simple webhook URL. No bot token or OAuth required.

Environment variables:
    DISCORD_WEBHOOK_URL — full Discord webhook URL

Usage:
    from agent.notify_discord import send_discord_alert, send_discord_digest

    send_discord_alert("High margin product found!", fields={...})
    send_discord_digest(opportunities)
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Optional

import httpx


# ---------------------------------------------------------------------------
# Colour constants for Discord embeds (decimal, not hex)
# ---------------------------------------------------------------------------

COLOR_PROFIT = 0x10B981    # emerald green
COLOR_LOSS = 0xF87171      # soft red
COLOR_INFO = 0x6366F1      # indigo
COLOR_WARNING = 0xF59E0B   # amber


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_webhook_url(
    webhook_url: Optional[str] = None,
    env: Optional[dict] = None,
) -> str:
    """Resolve webhook URL from arg or environment."""
    env = env or os.environ
    url = webhook_url or env.get("DISCORD_WEBHOOK_URL", "")
    if not url:
        raise ValueError(
            "Discord webhook URL is required. "
            "Set DISCORD_WEBHOOK_URL or pass webhook_url."
        )
    return url


def _timestamp_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _post_webhook(url: str, payload: dict) -> dict:
    """Send a payload to a Discord webhook. Returns the response data."""
    response = httpx.post(
        url,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=15.0,
    )
    # Discord returns 204 No Content on success for webhooks without ?wait=true
    if response.status_code == 204:
        return {"ok": True}
    response.raise_for_status()
    return response.json() if response.content else {"ok": True}


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------

def send_discord_message(
    content: str,
    *,
    webhook_url: Optional[str] = None,
    username: str = "DropAgent",
    env: Optional[dict] = None,
) -> dict:
    """Send a simple text message to Discord."""
    url = _resolve_webhook_url(webhook_url, env)
    return _post_webhook(url, {
        "username": username,
        "content": content,
    })


def send_discord_alert(
    title: str,
    description: str = "",
    *,
    fields: Optional[dict[str, Any]] = None,
    color: int = COLOR_INFO,
    webhook_url: Optional[str] = None,
    username: str = "DropAgent",
    env: Optional[dict] = None,
) -> dict:
    """
    Send a rich embed alert to Discord.

    Args:
        title: Embed title (e.g. "High Margin Product Detected!")
        description: Optional body text.
        fields: Dict of field_name → value to display in the embed.
        color: Embed sidebar colour (use COLOR_* constants).
        webhook_url: Override webhook URL.
        username: Bot display name in Discord.
    """
    url = _resolve_webhook_url(webhook_url, env)

    embed: dict[str, Any] = {
        "title": title,
        "color": color,
        "timestamp": _timestamp_iso(),
        "footer": {"text": "DropAgent"},
    }
    if description:
        embed["description"] = description

    if fields:
        embed["fields"] = [
            {"name": str(k), "value": str(v), "inline": True}
            for k, v in fields.items()
        ]

    return _post_webhook(url, {
        "username": username,
        "embeds": [embed],
    })


def send_discord_digest(
    opportunities: list[dict],
    *,
    title: str = "📊 Daily Digest",
    webhook_url: Optional[str] = None,
    username: str = "DropAgent",
    env: Optional[dict] = None,
) -> dict:
    """
    Send a digest summary as a rich Discord embed.

    Each opportunity dict should have: query, buy_price, sell_price,
    net_profit, margin_percent, score.
    """
    url = _resolve_webhook_url(webhook_url, env)

    if not opportunities:
        return send_discord_message(
            "📊 Daily Digest: No profitable opportunities found today.",
            webhook_url=url,
            username=username,
        )

    # Summary stats
    profits = [o.get("net_profit", 0) for o in opportunities]
    best = max(profits) if profits else 0
    avg = sum(profits) / len(profits) if profits else 0

    # Top 10 items as embed fields
    top = opportunities[:10]
    lines = []
    for i, opp in enumerate(top, 1):
        query = opp.get("query", "?")
        profit = opp.get("net_profit", 0)
        margin = opp.get("margin_percent", 0)
        lines.append(f"**{i}.** {query} — ${profit:.2f} ({margin:.1f}%)")

    description = "\n".join(lines)
    if len(opportunities) > 10:
        description += f"\n\n*...and {len(opportunities) - 10} more*"

    embed: dict[str, Any] = {
        "title": title,
        "description": description,
        "color": COLOR_PROFIT if best > 0 else COLOR_LOSS,
        "timestamp": _timestamp_iso(),
        "footer": {"text": "DropAgent"},
        "fields": [
            {"name": "Products", "value": str(len(opportunities)), "inline": True},
            {"name": "Best Profit", "value": f"${best:.2f}", "inline": True},
            {"name": "Avg Profit", "value": f"${avg:.2f}", "inline": True},
        ],
    }

    return _post_webhook(url, {
        "username": username,
        "embeds": [embed],
    })


def send_discord_margin_result(
    result: dict,
    *,
    webhook_url: Optional[str] = None,
    username: str = "DropAgent",
    env: Optional[dict] = None,
) -> dict:
    """Send a single margin calculation result as a Discord embed."""
    url = _resolve_webhook_url(webhook_url, env)
    profitable = result.get("is_profitable", False)
    status = "✅ PROFIT" if profitable else "❌ LOSS"
    color = COLOR_PROFIT if profitable else COLOR_LOSS

    embed: dict[str, Any] = {
        "title": f"Margin Calculator — {status}",
        "color": color,
        "timestamp": _timestamp_iso(),
        "footer": {"text": "DropAgent"},
        "fields": [
            {"name": "Buy Price", "value": f"${result.get('buy_price', 0):.2f}", "inline": True},
            {"name": "Sell Price", "value": f"${result.get('sell_price', 0):.2f}", "inline": True},
            {"name": "Net Profit", "value": f"${result.get('net_profit', 0):.2f}", "inline": True},
            {"name": "Margin", "value": f"{result.get('margin_percent', 0):.2f}%", "inline": True},
            {"name": "ROI", "value": f"{result.get('roi_percent', 0):.2f}%", "inline": True},
            {"name": "Markup", "value": f"{result.get('markup', 0):.2f}x", "inline": True},
            {"name": "Total Fees", "value": f"${result.get('total_fees', 0):.2f}", "inline": True},
            {"name": "Platform", "value": result.get("platform", "ebay"), "inline": True},
        ],
    }

    return _post_webhook(url, {
        "username": username,
        "embeds": [embed],
    })
