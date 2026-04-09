"""
Google Sheets export module for DropAgent.

Exports digest results, tracked queries, watchlist items, and margin
calculations to a Google Sheets spreadsheet using a service-account
credential file.

Environment variables:
    GOOGLE_SHEETS_CREDENTIALS  — path to service-account JSON key file
    GOOGLE_SHEETS_SPREADSHEET_ID — target spreadsheet ID (from URL)

Usage:
    from agent.export_sheets import export_digest, export_watchlist

    export_digest(rows, spreadsheet_id="...", credentials_path="...")
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Google API helpers — lazy-imported so the module is importable without
# the google client libraries installed (they're optional deps).
# ---------------------------------------------------------------------------

_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _get_sheets_service(credentials_path: str):
    """Build an authorized Google Sheets API service."""
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise ImportError(
            "google-api-python-client and google-auth are required for "
            "Sheets export. Install with:\n"
            "  pip install google-api-python-client google-auth"
        ) from exc

    creds = Credentials.from_service_account_file(credentials_path, scopes=_SCOPES)
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


def _resolve_env(
    credentials_path: Optional[str] = None,
    spreadsheet_id: Optional[str] = None,
    env: Optional[dict] = None,
) -> tuple[str, str]:
    """Resolve credentials path and spreadsheet ID from args or env."""
    env = env or os.environ
    creds = credentials_path or env.get("GOOGLE_SHEETS_CREDENTIALS", "")
    sheet_id = spreadsheet_id or env.get("GOOGLE_SHEETS_SPREADSHEET_ID", "")

    if not creds:
        raise ValueError(
            "Google Sheets credentials path is required. "
            "Set GOOGLE_SHEETS_CREDENTIALS or pass credentials_path."
        )
    if not sheet_id:
        raise ValueError(
            "Google Sheets spreadsheet ID is required. "
            "Set GOOGLE_SHEETS_SPREADSHEET_ID or pass spreadsheet_id."
        )
    if not Path(creds).exists():
        raise FileNotFoundError(f"Credentials file not found: {creds}")

    return creds, sheet_id


# ---------------------------------------------------------------------------
# Core write helper
# ---------------------------------------------------------------------------


def _write_to_sheet(
    service,
    spreadsheet_id: str,
    sheet_name: str,
    headers: list[str],
    rows: list[list[Any]],
    *,
    clear_first: bool = True,
) -> dict:
    """
    Write header + data rows to a named sheet tab.

    Creates the tab if it doesn't exist. Optionally clears old data first.
    Returns the Sheets API update response.
    """
    sheets = service.spreadsheets()

    # Ensure the sheet tab exists
    meta = sheets.get(spreadsheetId=spreadsheet_id).execute()
    existing = {s["properties"]["title"] for s in meta.get("sheets", [])}
    if sheet_name not in existing:
        sheets.batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": [{"addSheet": {"properties": {"title": sheet_name}}}]},
        ).execute()

    range_name = f"{sheet_name}!A1"

    if clear_first:
        sheets.values().clear(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!A:ZZ",
            body={},
        ).execute()

    # Write headers + rows
    body = {"values": [headers] + rows}
    return (
        sheets.values()
        .update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="USER_ENTERED",
            body=body,
        )
        .execute()
    )


# ---------------------------------------------------------------------------
# Public export functions
# ---------------------------------------------------------------------------

def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def export_digest(
    opportunities: list[dict],
    *,
    credentials_path: Optional[str] = None,
    spreadsheet_id: Optional[str] = None,
    sheet_name: str = "Digest",
    env: Optional[dict] = None,
) -> dict:
    """
    Export daily digest opportunities to a Google Sheet.

    Each opportunity dict should have keys like:
        query, source, buy_price, sell_price, net_profit, margin_percent, score
    """
    creds, sid = _resolve_env(credentials_path, spreadsheet_id, env)
    service = _get_sheets_service(creds)

    headers = [
        "Exported At",
        "Query",
        "Source",
        "Buy Price",
        "Sell Price",
        "Net Profit",
        "Margin %",
        "ROI %",
        "Score",
    ]
    rows = []
    ts = _timestamp()
    for opp in opportunities:
        rows.append([
            ts,
            opp.get("query", ""),
            opp.get("source", ""),
            opp.get("buy_price", ""),
            opp.get("sell_price", ""),
            opp.get("net_profit", ""),
            opp.get("margin_percent", ""),
            opp.get("roi_percent", ""),
            opp.get("score", ""),
        ])

    return _write_to_sheet(service, sid, sheet_name, headers, rows)


def export_margin_results(
    results: list[dict],
    *,
    credentials_path: Optional[str] = None,
    spreadsheet_id: Optional[str] = None,
    sheet_name: str = "Margin Calculations",
    env: Optional[dict] = None,
) -> dict:
    """Export a list of MarginResult.to_dict() objects to a sheet."""
    creds, sid = _resolve_env(credentials_path, spreadsheet_id, env)
    service = _get_sheets_service(creds)

    headers = [
        "Exported At",
        "Buy Price",
        "Sell Price",
        "Shipping",
        "Packaging",
        "Platform Fee",
        "Payment Fee",
        "Total Fees",
        "Total Cost",
        "Net Profit",
        "Margin %",
        "ROI %",
        "Markup",
        "Platform",
        "Model",
        "Profitable?",
    ]
    rows = []
    ts = _timestamp()
    for r in results:
        rows.append([
            ts,
            r.get("buy_price", ""),
            r.get("sell_price", ""),
            r.get("shipping_cost", ""),
            r.get("packaging_cost", ""),
            r.get("platform_fee", ""),
            r.get("payment_fee", ""),
            r.get("total_fees", ""),
            r.get("total_cost", ""),
            r.get("net_profit", ""),
            r.get("margin_percent", ""),
            r.get("roi_percent", ""),
            r.get("markup", ""),
            r.get("platform", ""),
            r.get("business_model", ""),
            "Yes" if r.get("is_profitable") else "No",
        ])

    return _write_to_sheet(service, sid, sheet_name, headers, rows)


def export_tracked_queries(
    queries: list[dict],
    *,
    credentials_path: Optional[str] = None,
    spreadsheet_id: Optional[str] = None,
    sheet_name: str = "Tracked Queries",
    env: Optional[dict] = None,
) -> dict:
    """Export tracked queries to a sheet."""
    creds, sid = _resolve_env(credentials_path, spreadsheet_id, env)
    service = _get_sheets_service(creds)

    headers = [
        "Exported At",
        "Query",
        "Category",
        "Min Profit Threshold",
        "Max Buy Price",
    ]
    rows = []
    ts = _timestamp()
    for q in queries:
        rows.append([
            ts,
            q.get("query", ""),
            q.get("category", ""),
            q.get("min_profit_threshold", ""),
            q.get("max_buy_price", ""),
        ])

    return _write_to_sheet(service, sid, sheet_name, headers, rows)


def export_watchlist(
    items: list[dict],
    *,
    credentials_path: Optional[str] = None,
    spreadsheet_id: Optional[str] = None,
    sheet_name: str = "Watchlist",
    env: Optional[dict] = None,
) -> dict:
    """Export watchlist items to a sheet."""
    creds, sid = _resolve_env(credentials_path, spreadsheet_id, env)
    service = _get_sheets_service(creds)

    headers = [
        "Exported At",
        "Item ID",
        "Product Name",
        "Source",
        "Buy Price",
        "Sell Price",
        "URL",
        "Price Points",
    ]
    rows = []
    ts = _timestamp()
    for item in items:
        rows.append([
            ts,
            item.get("item_id", ""),
            item.get("product_name", ""),
            item.get("source", ""),
            item.get("current_buy_price", ""),
            item.get("current_sell_price", ""),
            item.get("product_url", ""),
            len(item.get("price_history", [])),
        ])

    return _write_to_sheet(service, sid, sheet_name, headers, rows)
