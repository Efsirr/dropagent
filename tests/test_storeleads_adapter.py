"""Tests for StoreLeads adapter."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from agent.adapters.storeleads import (
    StoreApp,
    StoreContact,
    StoreDomain,
    StoreLeadsAdapter,
    get_storeleads_adapter_for_user,
)


class TestStoreContact:
    def test_to_dict_basic(self):
        c = StoreContact(contact_type="email", value="hello@shop.com")
        d = c.to_dict()
        assert d["type"] == "email"
        assert d["value"] == "hello@shop.com"
        assert "followers" not in d

    def test_to_dict_with_followers(self):
        c = StoreContact(contact_type="tiktok", value="https://tiktok.com/@shop", followers=50000, followers_30d=2000)
        d = c.to_dict()
        assert d["followers"] == 50000
        assert d["followers_30d"] == 2000


class TestStoreApp:
    def test_to_dict(self):
        a = StoreApp(name="Klaviyo", token="klaviyo", platform="shopify", installs=50000, rating="4.6")
        d = a.to_dict()
        assert d["name"] == "Klaviyo"
        assert d["installs"] == 50000


class TestStoreDomain:
    def test_to_dict(self):
        store = StoreDomain(
            domain="www.aloyoga.com",
            merchant_name="Alo Yoga",
            platform="shopify",
            product_count=3394,
            avg_price_usd=151.48,
            rank=206,
        )
        d = store.to_dict()
        assert d["domain"] == "www.aloyoga.com"
        assert d["merchant_name"] == "Alo Yoga"
        assert d["product_count"] == 3394
        assert d["avg_price_usd"] == 151.48
        assert isinstance(d["contacts"], list)
        assert isinstance(d["apps"], list)


class TestStoreLeadsAdapter:
    def test_requires_api_key(self):
        with pytest.raises(ValueError, match="required"):
            StoreLeadsAdapter(api_key="")

    def test_init(self):
        adapter = StoreLeadsAdapter(api_key="test_key")
        assert adapter._api_key == "test_key"

    def test_parse_domain_full(self):
        adapter = StoreLeadsAdapter(api_key="test")
        item = {
            "name": "www.testshop.com",
            "merchant_name": "Test Shop",
            "platform": "shopify",
            "plan": "Basic",
            "state": "Active",
            "country_code": "US",
            "currency_code": "USD",
            "location": "New York, NY, USA",
            "description": "A test store.",
            "product_count": 100,
            "avg_price_usd": 2500,      # cents → $25.00
            "min_price_usd": 500,       # cents → $5.00
            "max_price_usd": 10000,     # cents → $100.00
            "vendor_count": 5,
            "estimated_visits": 50000,
            "estimated_sales": 10000000,  # cents → $100,000.00
            "rank": 5000,
            "platform_rank": 1000,
            "contact_info": [
                {"type": "email", "value": "hello@testshop.com"},
                {"type": "tiktok", "value": "https://tiktok.com/@shop", "followers": 10000},
            ],
            "apps": [
                {"name": "Klaviyo", "token": "klaviyo", "platform": "shopify", "installs": 50000, "average_rating": "4.6"},
            ],
            "categories": ["/Beauty & Fitness/Fitness"],
            "features": ["Contact Page", "Free Returns"],
        }
        result = adapter._parse_domain(item)
        assert result.domain == "www.testshop.com"
        assert result.merchant_name == "Test Shop"
        assert result.platform == "shopify"
        assert result.avg_price_usd == 25.0
        assert result.min_price_usd == 5.0
        assert result.max_price_usd == 100.0
        assert result.estimated_sales_monthly_usd == 100000.0
        assert len(result.contacts) == 2
        assert result.contacts[1].followers == 10000
        assert len(result.apps) == 1
        assert result.apps[0].name == "Klaviyo"

    def test_parse_domain_minimal(self):
        adapter = StoreLeadsAdapter(api_key="test")
        result = adapter._parse_domain({"name": "minimal.com"})
        assert result.domain == "minimal.com"
        assert result.product_count is None
        assert result.contacts == []


class TestGetStoreLeadsAdapterForUser:
    @patch.dict("os.environ", {"APP_SECRET_KEY": ""})
    def test_missing_app_secret(self):
        result = get_storeleads_adapter_for_user("12345", MagicMock(), app_secret="")
        assert result is None

    @patch("db.service.get_user_integration_encrypted_secret", return_value=None)
    def test_no_saved_key(self, mock_get):
        result = get_storeleads_adapter_for_user(
            "12345", MagicMock(), app_secret="test_secret_key_1234567890"
        )
        assert result is None

    @patch("agent.secrets.open_secret", return_value="real_storeleads_key")
    @patch("db.service.get_user_integration_encrypted_secret", return_value="da1.blob")
    def test_success(self, mock_get, mock_open):
        result = get_storeleads_adapter_for_user(
            "12345", MagicMock(), app_secret="test_secret_key_1234567890"
        )
        assert result is not None
        assert isinstance(result, StoreLeadsAdapter)
        assert result._api_key == "real_storeleads_key"

    @patch("agent.secrets.open_secret", side_effect=Exception("decrypt error"))
    @patch("db.service.get_user_integration_encrypted_secret", return_value="da1.bad")
    def test_decrypt_failure(self, mock_get, mock_open):
        result = get_storeleads_adapter_for_user(
            "12345", MagicMock(), app_secret="test_secret_key_1234567890"
        )
        assert result is None
