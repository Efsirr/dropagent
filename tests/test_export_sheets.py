"""Tests for agent.export_sheets — Google Sheets export module."""

from __future__ import annotations

import json
from datetime import datetime
from unittest.mock import MagicMock, patch, call

import pytest

from agent.export_sheets import (
    _resolve_env,
    _write_to_sheet,
    export_digest,
    export_margin_results,
    export_tracked_queries,
    export_watchlist,
)


# ---------------------------------------------------------------------------
# _resolve_env tests
# ---------------------------------------------------------------------------


class TestResolveEnv:
    """Tests for environment variable resolution."""

    def test_resolve_from_args(self, tmp_path):
        creds_file = tmp_path / "creds.json"
        creds_file.write_text("{}")
        creds, sid = _resolve_env(
            credentials_path=str(creds_file),
            spreadsheet_id="abc123",
        )
        assert creds == str(creds_file)
        assert sid == "abc123"

    def test_resolve_from_env(self, tmp_path):
        creds_file = tmp_path / "creds.json"
        creds_file.write_text("{}")
        env = {
            "GOOGLE_SHEETS_CREDENTIALS": str(creds_file),
            "GOOGLE_SHEETS_SPREADSHEET_ID": "xyz789",
        }
        creds, sid = _resolve_env(env=env)
        assert creds == str(creds_file)
        assert sid == "xyz789"

    def test_missing_credentials_raises(self):
        with pytest.raises(ValueError, match="credentials path is required"):
            _resolve_env(spreadsheet_id="abc")

    def test_missing_spreadsheet_id_raises(self, tmp_path):
        creds_file = tmp_path / "creds.json"
        creds_file.write_text("{}")
        with pytest.raises(ValueError, match="spreadsheet ID is required"):
            _resolve_env(credentials_path=str(creds_file))

    def test_missing_credentials_file_raises(self):
        with pytest.raises(FileNotFoundError, match="not found"):
            _resolve_env(
                credentials_path="/nonexistent/creds.json",
                spreadsheet_id="abc",
            )

    def test_args_override_env(self, tmp_path):
        creds_file = tmp_path / "override.json"
        creds_file.write_text("{}")
        env = {
            "GOOGLE_SHEETS_CREDENTIALS": "/some/other.json",
            "GOOGLE_SHEETS_SPREADSHEET_ID": "env_id",
        }
        creds, sid = _resolve_env(
            credentials_path=str(creds_file),
            spreadsheet_id="arg_id",
            env=env,
        )
        assert creds == str(creds_file)
        assert sid == "arg_id"


# ---------------------------------------------------------------------------
# _write_to_sheet tests
# ---------------------------------------------------------------------------


class TestWriteToSheet:
    """Tests for the core sheet writer."""

    def _mock_service(self, existing_sheets=None):
        """Build a mock Sheets service."""
        if existing_sheets is None:
            existing_sheets = []

        service = MagicMock()
        spreadsheets = MagicMock()
        service.spreadsheets.return_value = spreadsheets

        # get() returns sheet metadata
        meta = {
            "sheets": [{"properties": {"title": t}} for t in existing_sheets]
        }
        spreadsheets.get.return_value.execute.return_value = meta

        # values().clear() and values().update()
        values = MagicMock()
        spreadsheets.values.return_value = values
        values.clear.return_value.execute.return_value = {}
        values.update.return_value.execute.return_value = {"updatedCells": 10}

        # batchUpdate for creating sheets
        spreadsheets.batchUpdate.return_value.execute.return_value = {}

        return service, spreadsheets

    def test_creates_new_sheet_if_missing(self):
        service, spreadsheets = self._mock_service(existing_sheets=["Other"])
        _write_to_sheet(service, "sid", "NewSheet", ["A"], [["1"]])

        # Should have called batchUpdate to add the sheet
        spreadsheets.batchUpdate.assert_called_once()
        body = spreadsheets.batchUpdate.call_args[1]["body"]
        assert body["requests"][0]["addSheet"]["properties"]["title"] == "NewSheet"

    def test_skips_creation_if_sheet_exists(self):
        service, spreadsheets = self._mock_service(existing_sheets=["Digest"])
        _write_to_sheet(service, "sid", "Digest", ["A"], [["1"]])
        spreadsheets.batchUpdate.assert_not_called()

    def test_clears_old_data_by_default(self):
        service, spreadsheets = self._mock_service(existing_sheets=["Test"])
        _write_to_sheet(service, "sid", "Test", ["Col1"], [["val1"]])
        spreadsheets.values().clear.assert_called_once()

    def test_skip_clear_when_disabled(self):
        service, spreadsheets = self._mock_service(existing_sheets=["Test"])
        _write_to_sheet(
            service, "sid", "Test", ["Col1"], [["val1"]], clear_first=False
        )
        spreadsheets.values().clear.assert_not_called()

    def test_writes_headers_and_rows(self):
        service, spreadsheets = self._mock_service(existing_sheets=["Test"])
        _write_to_sheet(service, "sid", "Test", ["A", "B"], [["1", "2"], ["3", "4"]])

        update_call = spreadsheets.values().update
        update_call.assert_called_once()
        body = update_call.call_args[1]["body"]
        assert body["values"] == [["A", "B"], ["1", "2"], ["3", "4"]]


# ---------------------------------------------------------------------------
# Export function tests (mock the Google API)
# ---------------------------------------------------------------------------


class TestExportDigest:
    """Tests for export_digest."""

    @patch("agent.export_sheets._get_sheets_service")
    def test_export_digest_basic(self, mock_get_service, tmp_path):
        creds = tmp_path / "creds.json"
        creds.write_text("{}")

        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        sheets = MagicMock()
        mock_service.spreadsheets.return_value = sheets
        sheets.get.return_value.execute.return_value = {"sheets": [{"properties": {"title": "Digest"}}]}
        sheets.values.return_value.clear.return_value.execute.return_value = {}
        sheets.values.return_value.update.return_value.execute.return_value = {"updatedCells": 5}

        opportunities = [
            {"query": "airpods", "source": "amazon", "buy_price": 25, "sell_price": 50,
             "net_profit": 15, "margin_percent": 30, "roi_percent": 60, "score": 85},
        ]

        result = export_digest(
            opportunities,
            credentials_path=str(creds),
            spreadsheet_id="test_id",
        )
        assert result["updatedCells"] == 5

    @patch("agent.export_sheets._get_sheets_service")
    def test_export_empty_digest(self, mock_get_service, tmp_path):
        creds = tmp_path / "creds.json"
        creds.write_text("{}")

        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        sheets = MagicMock()
        mock_service.spreadsheets.return_value = sheets
        sheets.get.return_value.execute.return_value = {"sheets": [{"properties": {"title": "Digest"}}]}
        sheets.values.return_value.clear.return_value.execute.return_value = {}
        sheets.values.return_value.update.return_value.execute.return_value = {"updatedCells": 1}

        result = export_digest([], credentials_path=str(creds), spreadsheet_id="test_id")
        assert result["updatedCells"] == 1


class TestExportMarginResults:
    """Tests for export_margin_results."""

    @patch("agent.export_sheets._get_sheets_service")
    def test_export_margin(self, mock_get_service, tmp_path):
        creds = tmp_path / "creds.json"
        creds.write_text("{}")

        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        sheets = MagicMock()
        mock_service.spreadsheets.return_value = sheets
        sheets.get.return_value.execute.return_value = {"sheets": []}
        sheets.batchUpdate.return_value.execute.return_value = {}
        sheets.values.return_value.clear.return_value.execute.return_value = {}
        sheets.values.return_value.update.return_value.execute.return_value = {"updatedCells": 3}

        results = [
            {"buy_price": 25, "sell_price": 50, "shipping_cost": 5, "packaging_cost": 1.5,
             "platform_fee": 6.5, "payment_fee": 1.75, "total_fees": 8.25, "total_cost": 39.75,
             "net_profit": 10.25, "margin_percent": 20.5, "roi_percent": 41.0, "markup": 2.0,
             "platform": "ebay", "business_model": "us_arbitrage", "is_profitable": True},
        ]

        result = export_margin_results(
            results, credentials_path=str(creds), spreadsheet_id="test_id"
        )
        assert result["updatedCells"] == 3


class TestExportTrackedQueries:
    """Tests for export_tracked_queries."""

    @patch("agent.export_sheets._get_sheets_service")
    def test_export_queries(self, mock_get_service, tmp_path):
        creds = tmp_path / "creds.json"
        creds.write_text("{}")

        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        sheets = MagicMock()
        mock_service.spreadsheets.return_value = sheets
        sheets.get.return_value.execute.return_value = {"sheets": [{"properties": {"title": "Tracked Queries"}}]}
        sheets.values.return_value.clear.return_value.execute.return_value = {}
        sheets.values.return_value.update.return_value.execute.return_value = {"updatedCells": 4}

        queries = [
            {"query": "airpods pro", "category": "electronics", "min_profit_threshold": 10, "max_buy_price": 80},
            {"query": "gaming mouse", "category": "", "min_profit_threshold": 5, "max_buy_price": None},
        ]

        result = export_tracked_queries(
            queries, credentials_path=str(creds), spreadsheet_id="test_id"
        )
        assert result["updatedCells"] == 4


class TestExportWatchlist:
    """Tests for export_watchlist."""

    @patch("agent.export_sheets._get_sheets_service")
    def test_export_watchlist(self, mock_get_service, tmp_path):
        creds = tmp_path / "creds.json"
        creds.write_text("{}")

        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        sheets = MagicMock()
        mock_service.spreadsheets.return_value = sheets
        sheets.get.return_value.execute.return_value = {"sheets": []}
        sheets.batchUpdate.return_value.execute.return_value = {}
        sheets.values.return_value.clear.return_value.execute.return_value = {}
        sheets.values.return_value.update.return_value.execute.return_value = {"updatedCells": 2}

        items = [
            {"item_id": 1, "product_name": "AirPods", "source": "amazon",
             "current_buy_price": 159.99, "current_sell_price": 229.99,
             "product_url": "https://example.com", "price_history": [{"buy": 160}]},
        ]

        result = export_watchlist(
            items, credentials_path=str(creds), spreadsheet_id="test_id"
        )
        assert result["updatedCells"] == 2
