"""
Email notification module for DropAgent.

Sends alerts, digest summaries, and margin results via SMTP.
Supports plain-text and HTML emails.

Environment variables:
    SMTP_HOST      — SMTP server hostname (e.g. smtp.gmail.com)
    SMTP_PORT      — SMTP port (default: 587 for STARTTLS)
    SMTP_USER      — SMTP login username
    SMTP_PASSWORD  — SMTP login password
    SMTP_FROM      — sender email address (defaults to SMTP_USER)
    SMTP_TO        — default recipient email address

Usage:
    from agent.notify_email import send_email, send_digest_email

    send_email("Test Subject", "Hello from DropAgent!")
    send_digest_email(opportunities)
"""

from __future__ import annotations

import os
import smtplib
import ssl
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Config resolver
# ---------------------------------------------------------------------------

def _resolve_smtp_config(
    env: Optional[dict] = None,
    **overrides: Any,
) -> dict:
    """Resolve SMTP config from environment + overrides."""
    env = env or os.environ
    config = {
        "host": overrides.get("host") or env.get("SMTP_HOST", ""),
        "port": int(overrides.get("port") or env.get("SMTP_PORT", "587")),
        "user": overrides.get("user") or env.get("SMTP_USER", ""),
        "password": overrides.get("password") or env.get("SMTP_PASSWORD", ""),
        "from_addr": overrides.get("from_addr") or env.get("SMTP_FROM", ""),
        "to_addr": overrides.get("to_addr") or env.get("SMTP_TO", ""),
    }
    # Default from_addr to user if not set
    if not config["from_addr"]:
        config["from_addr"] = config["user"]

    if not config["host"]:
        raise ValueError(
            "SMTP host is required. Set SMTP_HOST or pass host= argument."
        )
    if not config["user"] or not config["password"]:
        raise ValueError(
            "SMTP credentials are required. Set SMTP_USER and SMTP_PASSWORD."
        )
    if not config["to_addr"]:
        raise ValueError(
            "Recipient email is required. Set SMTP_TO or pass to_addr= argument."
        )

    return config


# ---------------------------------------------------------------------------
# Core send function
# ---------------------------------------------------------------------------

def send_email(
    subject: str,
    body_text: str,
    body_html: Optional[str] = None,
    *,
    to_addr: Optional[str] = None,
    env: Optional[dict] = None,
    **smtp_overrides: Any,
) -> dict:
    """
    Send an email via SMTP.

    Args:
        subject: Email subject line.
        body_text: Plain-text body (always included as fallback).
        body_html: Optional HTML body for rich formatting.
        to_addr: Recipient email (overrides SMTP_TO).
        env: Environment dict override.
        **smtp_overrides: host, port, user, password, from_addr overrides.

    Returns:
        Dict with status info.
    """
    if to_addr:
        smtp_overrides["to_addr"] = to_addr

    config = _resolve_smtp_config(env=env, **smtp_overrides)

    # Build the message
    if body_html:
        msg = MIMEMultipart("alternative")
        msg.attach(MIMEText(body_text, "plain", "utf-8"))
        msg.attach(MIMEText(body_html, "html", "utf-8"))
    else:
        msg = MIMEMultipart()
        msg.attach(MIMEText(body_text, "plain", "utf-8"))

    msg["Subject"] = subject
    msg["From"] = config["from_addr"]
    msg["To"] = config["to_addr"]

    # Send via STARTTLS
    context = ssl.create_default_context()

    with smtplib.SMTP(config["host"], config["port"], timeout=30) as server:
        server.starttls(context=context)
        server.login(config["user"], config["password"])
        server.send_message(msg)

    return {
        "ok": True,
        "to": config["to_addr"],
        "subject": subject,
    }


# ---------------------------------------------------------------------------
# Formatted senders
# ---------------------------------------------------------------------------

def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def send_alert_email(
    title: str,
    message: str,
    *,
    to_addr: Optional[str] = None,
    env: Optional[dict] = None,
    **smtp_overrides: Any,
) -> dict:
    """Send a simple alert notification email."""
    subject = f"[DropAgent] {title}"

    body_text = (
        f"{title}\n"
        f"{'=' * 40}\n\n"
        f"{message}\n\n"
        f"— DropAgent ({_timestamp()})"
    )

    body_html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                max-width: 600px; margin: 0 auto; padding: 24px;
                background: #1a1a2e; color: #e0e0e0; border-radius: 12px;">
        <h2 style="color: #10b981; margin-top: 0;">🔔 {_escape(title)}</h2>
        <p style="line-height: 1.6;">{_escape(message)}</p>
        <hr style="border: 1px solid #333; margin: 20px 0;">
        <p style="color: #888; font-size: 12px;">DropAgent · {_timestamp()}</p>
    </div>
    """

    return send_email(
        subject, body_text, body_html,
        to_addr=to_addr, env=env, **smtp_overrides,
    )


def send_digest_email(
    opportunities: list[dict],
    *,
    title: str = "Daily Digest",
    to_addr: Optional[str] = None,
    env: Optional[dict] = None,
    **smtp_overrides: Any,
) -> dict:
    """
    Send a formatted digest report via email.

    Each opportunity dict should have: query, buy_price, sell_price,
    net_profit, margin_percent, score.
    """
    subject = f"[DropAgent] {title} — {_timestamp()}"
    ts = _timestamp()

    if not opportunities:
        return send_email(
            subject,
            f"No profitable opportunities found.\n\n— DropAgent ({ts})",
            to_addr=to_addr, env=env, **smtp_overrides,
        )

    # Summary stats
    profits = [o.get("net_profit", 0) for o in opportunities]
    best = max(profits) if profits else 0
    avg = sum(profits) / len(profits) if profits else 0

    # Plain text
    lines = [
        f"{title}",
        f"{'=' * 50}",
        f"Products: {len(opportunities)} | Best: ${best:.2f} | Avg: ${avg:.2f}",
        "",
    ]
    for i, opp in enumerate(opportunities[:20], 1):
        query = opp.get("query", "?")
        profit = opp.get("net_profit", 0)
        margin = opp.get("margin_percent", 0)
        buy = opp.get("buy_price", 0)
        sell = opp.get("sell_price", 0)
        lines.append(
            f"{i:>3}. {query:<30} "
            f"Buy: ${buy:<8.2f} Sell: ${sell:<8.2f} "
            f"Profit: ${profit:<8.2f} Margin: {margin:.1f}%"
        )
    if len(opportunities) > 20:
        lines.append(f"\n...and {len(opportunities) - 20} more opportunities")
    lines.append(f"\n— DropAgent ({ts})")
    body_text = "\n".join(lines)

    # HTML
    rows_html = ""
    for i, opp in enumerate(opportunities[:20], 1):
        query = opp.get("query", "?")
        profit = opp.get("net_profit", 0)
        margin = opp.get("margin_percent", 0)
        buy = opp.get("buy_price", 0)
        sell = opp.get("sell_price", 0)
        profit_color = "#10b981" if profit > 0 else "#f87171"
        rows_html += f"""
        <tr style="border-bottom: 1px solid #333;">
            <td style="padding: 8px;">{i}</td>
            <td style="padding: 8px;">{_escape(query)}</td>
            <td style="padding: 8px;">${buy:.2f}</td>
            <td style="padding: 8px;">${sell:.2f}</td>
            <td style="padding: 8px; color: {profit_color}; font-weight: 600;">${profit:.2f}</td>
            <td style="padding: 8px;">{margin:.1f}%</td>
        </tr>
        """

    body_html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                max-width: 700px; margin: 0 auto; padding: 24px;
                background: #1a1a2e; color: #e0e0e0; border-radius: 12px;">
        <h2 style="color: #10b981; margin-top: 0;">📊 {_escape(title)}</h2>
        <div style="display: flex; gap: 16px; margin-bottom: 20px;">
            <div style="background: #222; padding: 12px 16px; border-radius: 8px; flex: 1; text-align: center;">
                <div style="font-size: 24px; font-weight: 700;">{len(opportunities)}</div>
                <div style="color: #888; font-size: 12px;">Products</div>
            </div>
            <div style="background: #222; padding: 12px 16px; border-radius: 8px; flex: 1; text-align: center;">
                <div style="font-size: 24px; font-weight: 700; color: #10b981;">${best:.2f}</div>
                <div style="color: #888; font-size: 12px;">Best Profit</div>
            </div>
            <div style="background: #222; padding: 12px 16px; border-radius: 8px; flex: 1; text-align: center;">
                <div style="font-size: 24px; font-weight: 700;">${avg:.2f}</div>
                <div style="color: #888; font-size: 12px;">Avg Profit</div>
            </div>
        </div>
        <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
            <thead>
                <tr style="border-bottom: 2px solid #444; text-align: left;">
                    <th style="padding: 8px;">#</th>
                    <th style="padding: 8px;">Product</th>
                    <th style="padding: 8px;">Buy</th>
                    <th style="padding: 8px;">Sell</th>
                    <th style="padding: 8px;">Profit</th>
                    <th style="padding: 8px;">Margin</th>
                </tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
        {"<p style='color: #888;'>...and " + str(len(opportunities) - 20) + " more</p>" if len(opportunities) > 20 else ""}
        <hr style="border: 1px solid #333; margin: 20px 0;">
        <p style="color: #888; font-size: 12px;">DropAgent · {ts}</p>
    </div>
    """

    return send_email(
        subject, body_text, body_html,
        to_addr=to_addr, env=env, **smtp_overrides,
    )


def send_margin_email(
    result: dict,
    *,
    to_addr: Optional[str] = None,
    env: Optional[dict] = None,
    **smtp_overrides: Any,
) -> dict:
    """Send a single margin calculation result via email."""
    profitable = result.get("is_profitable", False)
    status = "PROFIT" if profitable else "LOSS"
    subject = f"[DropAgent] Margin Calc — {status} ${abs(result.get('net_profit', 0)):.2f}"

    body_text = (
        f"Margin Calculator — {status}\n"
        f"{'=' * 40}\n"
        f"Buy Price:    ${result.get('buy_price', 0):.2f}\n"
        f"Sell Price:   ${result.get('sell_price', 0):.2f}\n"
        f"Net Profit:   ${result.get('net_profit', 0):.2f}\n"
        f"Margin:       {result.get('margin_percent', 0):.2f}%\n"
        f"ROI:          {result.get('roi_percent', 0):.2f}%\n"
        f"Markup:       {result.get('markup', 0):.2f}x\n"
        f"Total Fees:   ${result.get('total_fees', 0):.2f}\n"
        f"Platform:     {result.get('platform', 'ebay')}\n"
        f"\n— DropAgent ({_timestamp()})"
    )

    return send_email(
        subject, body_text,
        to_addr=to_addr, env=env, **smtp_overrides,
    )


def _escape(text: str) -> str:
    """Escape HTML special characters."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
