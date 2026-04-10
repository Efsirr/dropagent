"""Tests for the Keepa adapter."""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.adapters.keepa import (
    KeepaAdapter,
    KeepaProduct,
    PricePoint,
    _compute_stats,
    _parse_csv_pairs,
    datetime_to_keepa_time,
    get_keepa_adapter_for_user,
    keepa_time_to_datetime,
    _KEEPA_EPOCH,
)


# ── Time conversion tests ────────────────────────────────────────────

class TestTimeConversion:
    def test_keepa_epoch(self):
        """Keepa time 0 maps to 2011-01-01 00:00 UTC."""
        result = keepa_time_to_datetime(0)
        assert result == datetime(2011, 1, 1, tzinfo=timezone.utc)

    def test_roundtrip(self):
        """Convert to Keepa time and back."""
        now = datetime(2024, 6, 15, 12, 30, tzinfo=timezone.utc)
        keepa_time = datetime_to_keepa_time(now)
        result = keepa_time_to_datetime(keepa_time)
        # Round-trip to minute precision
        assert abs((result - now).total_seconds()) < 60

    def test_known_value(self):
        """24 hours after epoch = 1440 Keepa minutes."""
        result = keepa_time_to_datetime(1440)
        expected = _KEEPA_EPOCH + timedelta(days=1)
        assert result == expected


# ── CSV parsing tests ─────────────────────────────────────────────────

class TestParseCsvPairs:
    def test_empty_array(self):
        assert _parse_csv_pairs([], "amazon") == []

    def test_basic_pairs(self):
        """Parse two time-value pairs."""
        csv = [100, 2999, 200, 3499]
        result = _parse_csv_pairs(csv, "amazon")
        assert len(result) == 2
        assert result[0].price_usd == 29.99
        assert result[0].price_type == "amazon"
        assert result[1].price_usd == 34.99

    def test_out_of_stock_marker(self):
        """Value -1 means out of stock → price_usd is None."""
        csv = [100, -1, 200, 1999]
        result = _parse_csv_pairs(csv, "new")
        assert result[0].price_usd is None
        assert result[1].price_usd == 19.99

    def test_non_price_mode(self):
        """Sales rank uses raw values without dividing by 100."""
        csv = [100, 5000, 200, 3000]
        result = _parse_csv_pairs(csv, "sales_rank", is_price=False)
        assert result[0].price_usd == 5000.0
        assert result[1].price_usd == 3000.0

    def test_odd_length_ignored(self):
        """If array has odd length, last unpaired element is ignored."""
        csv = [100, 2999, 200]  # 200 has no pair
        result = _parse_csv_pairs(csv, "amazon")
        assert len(result) == 1


# ── Stats computation tests ──────────────────────────────────────────

class TestComputeStats:
    def test_empty_history(self):
        stats = _compute_stats([])
        assert stats["price_30d_avg"] is None
        assert stats["price_90d_avg"] is None
        assert stats["price_drops_90d"] == 0

    def test_recent_prices(self):
        now = datetime(2024, 6, 15, tzinfo=timezone.utc)
        points = [
            PricePoint(now - timedelta(days=10), 29.99, "amazon"),
            PricePoint(now - timedelta(days=20), 34.99, "amazon"),
            PricePoint(now - timedelta(days=5), 24.99, "amazon"),
        ]
        stats = _compute_stats(points, now=now)
        assert stats["price_30d_avg"] == pytest.approx(29.99, abs=0.01)
        assert stats["price_30d_min"] == 24.99
        assert stats["price_30d_max"] == 34.99

    def test_price_drops_counted(self):
        now = datetime(2024, 6, 15, tzinfo=timezone.utc)
        # 50 → 30 is a 40% drop (>5%), 30 → 28 is 6.7% drop (>5%)
        points = [
            PricePoint(now - timedelta(days=60), 50.0, "amazon"),
            PricePoint(now - timedelta(days=30), 30.0, "amazon"),
            PricePoint(now - timedelta(days=10), 28.0, "amazon"),
        ]
        stats = _compute_stats(points, now=now)
        assert stats["price_drops_90d"] == 2  # both drops are >5%

    def test_out_of_stock_excluded(self):
        now = datetime(2024, 6, 15, tzinfo=timezone.utc)
        points = [
            PricePoint(now - timedelta(days=10), None, "amazon"),
            PricePoint(now - timedelta(days=5), 19.99, "amazon"),
        ]
        stats = _compute_stats(points, now=now)
        assert stats["price_30d_avg"] == 19.99
        assert stats["price_30d_min"] == 19.99


# ── KeepaProduct tests ───────────────────────────────────────────────

class TestKeepaProduct:
    def test_to_dict(self):
        product = KeepaProduct(
            asin="B09V3KXJPB",
            title="Test Product",
            current_amazon_price=24.99,
        )
        d = product.to_dict()
        assert d["asin"] == "B09V3KXJPB"
        assert d["title"] == "Test Product"
        assert d["current_amazon_price"] == 24.99
        assert isinstance(d["amazon_history"], list)


# ── KeepaAdapter tests ───────────────────────────────────────────────

class TestKeepaAdapter:
    def test_requires_api_key(self):
        with pytest.raises(ValueError, match="required"):
            KeepaAdapter(api_key="")

    def test_init(self):
        adapter = KeepaAdapter(api_key="test_key_123")
        assert adapter._api_key == "test_key_123"
        assert adapter._domain_id == 1

    def test_parse_product(self):
        """Parse a Keepa API product response."""
        adapter = KeepaAdapter(api_key="test")
        item = {
            "asin": "B09V3KXJPB",
            "title": "Wireless Mouse",
            "brand": "Logitech",
            "categoryTree": [{"name": "Electronics"}],
            "salesRankCurrent": 1500,
            "csv": [
                [100, 2999, 200, 3499],  # index 0: Amazon
                [100, 2799, 200, 3299],  # index 1: New
            ] + [[] for _ in range(17)] + [  # pad to index 18
                [100, 2999, 200, 3499],  # index 18: Buy box (CSV_BUY_BOX)
            ],
            "stats": {
                "current": [2999, 2799] + [0] * 16 + [2999],
            },
        }
        result = adapter._parse_product(item)
        assert result is not None
        assert result.asin == "B09V3KXJPB"
        assert result.title == "Wireless Mouse"
        assert result.brand == "Logitech"
        assert result.category == "Electronics"
        assert result.sales_rank == 1500
        assert result.current_amazon_price == 29.99
        assert result.current_new_price == 27.99
        assert len(result.amazon_history) == 2
        assert result.amazon_history[0].price_usd == 29.99

    def test_parse_product_missing_asin(self):
        adapter = KeepaAdapter(api_key="test")
        assert adapter._parse_product({}) is None

    def test_parse_product_empty_csv(self):
        adapter = KeepaAdapter(api_key="test")
        result = adapter._parse_product({"asin": "B000TEST", "csv": []})
        assert result is not None
        assert result.asin == "B000TEST"
        assert result.amazon_history == []


# ── get_keepa_adapter_for_user tests ─────────────────────────────────

class TestGetKeepaAdapterForUser:
    @patch.dict("os.environ", {"APP_SECRET_KEY": ""})
    def test_missing_app_secret(self):
        """Returns None if APP_SECRET_KEY is not configured."""
        result = get_keepa_adapter_for_user("12345", MagicMock(), app_secret="")
        assert result is None

    @patch("db.service.get_user_integration_encrypted_secret", return_value=None)
    def test_no_saved_key(self, mock_get):
        """Returns None if user hasn't connected Keepa."""
        result = get_keepa_adapter_for_user(
            "12345", MagicMock(), app_secret="test_secret_key_1234567890"
        )
        assert result is None

    @patch("agent.secrets.open_secret", return_value="real_keepa_key")
    @patch(
        "db.service.get_user_integration_encrypted_secret",
        return_value="da1.encrypted_blob",
    )
    def test_success(self, mock_get, mock_open):
        """Returns an adapter when key is saved and decrypts."""
        result = get_keepa_adapter_for_user(
            "12345", MagicMock(), app_secret="test_secret_key_1234567890"
        )
        assert result is not None
        assert isinstance(result, KeepaAdapter)
        assert result._api_key == "real_keepa_key"

    @patch("agent.secrets.open_secret", side_effect=Exception("decrypt failed"))
    @patch(
        "db.service.get_user_integration_encrypted_secret",
        return_value="da1.corrupted",
    )
    def test_decrypt_failure(self, mock_get, mock_open):
        """Returns None if decryption fails."""
        result = get_keepa_adapter_for_user(
            "12345", MagicMock(), app_secret="test_secret_key_1234567890"
        )
        assert result is None
