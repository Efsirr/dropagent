"""Tests for PiPiADS adapter."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from agent.adapters.pipiads import (
    AdSearchResult,
    PiPiAdsAdapter,
    TikTokAd,
    compute_trend_score,
    get_pipiads_adapter_for_user,
)


class TestTikTokAd:
    def test_to_dict(self):
        ad = TikTokAd(
            ad_id="123",
            title="Dog Toy Ad",
            advertiser="PetShop",
            total_likes=5000,
            total_comments=200,
            total_shares=100,
            days_running=7,
        )
        d = ad.to_dict()
        assert d["ad_id"] == "123"
        assert d["title"] == "Dog Toy Ad"
        assert d["total_likes"] == 5000


class TestAdSearchResult:
    def test_to_dict(self):
        result = AdSearchResult(
            ads=[TikTokAd(ad_id="1", title="Test")],
            total_count=100,
            page=0,
        )
        d = result.to_dict()
        assert len(d["ads"]) == 1
        assert d["total_count"] == 100


class TestComputeTrendScore:
    def test_zero_engagement(self):
        ad = TikTokAd(ad_id="1", days_running=10)
        score = compute_trend_score(ad)
        assert score == 0.0

    def test_high_engagement(self):
        ad = TikTokAd(
            ad_id="1",
            total_likes=10000,
            total_comments=500,
            total_shares=200,
            days_running=5,
        )
        score = compute_trend_score(ad)
        assert score > 0
        # engagement = 10000 + 500*3 + 200*5 = 12500
        # per_day = 12500/5 = 2500
        # volume_bonus = log10(12501) ≈ 4.097
        # score ≈ 2500 * 4.097 ≈ 10242
        assert score > 1000

    def test_zero_days_uses_one(self):
        ad = TikTokAd(ad_id="1", total_likes=100, days_running=0)
        score = compute_trend_score(ad)
        assert score > 0


class TestPiPiAdsAdapter:
    def test_requires_api_key(self):
        with pytest.raises(ValueError, match="required"):
            PiPiAdsAdapter(api_key="")

    def test_init(self):
        adapter = PiPiAdsAdapter(api_key="test_key")
        assert adapter._api_key == "test_key"

    def test_parse_ad(self):
        adapter = PiPiAdsAdapter(api_key="test")
        item = {
            "id": "456",
            "title": "Viral Product",
            "advertiser": "TrendShop",
            "landing_page": "https://trend.shop/product",
            "country": "US",
            "likes": 15000,
            "comments": 800,
            "shares": 300,
            "impressions": 500000,
            "days_running": 14,
            "first_seen": "2024-01-01",
            "last_seen": "2024-01-15",
            "video_url": "https://video.tiktok.com/456.mp4",
            "thumbnail_url": "https://img.tiktok.com/456.jpg",
        }
        ad = adapter._parse_ad(item)
        assert ad.ad_id == "456"
        assert ad.title == "Viral Product"
        assert ad.total_likes == 15000
        assert ad.total_comments == 800
        assert ad.total_shares == 300
        assert ad.days_running == 14
        assert ad.trend_score is not None
        assert ad.trend_score > 0

    def test_parse_ad_alt_field_names(self):
        """Handles alternative field names from API variants."""
        adapter = PiPiAdsAdapter(api_key="test")
        item = {
            "ad_id": "789",
            "ad_title": "Alt Name Product",
            "advertiser_name": "AltShop",
            "url": "https://altshop.com",
            "total_likes": 1000,
            "total_comments": 50,
            "total_shares": 20,
            "duration": 7,
            "created_at": "2024-02-01",
            "updated_at": "2024-02-08",
            "cover_url": "https://img.com/cover.jpg",
        }
        ad = adapter._parse_ad(item)
        assert ad.ad_id == "789"
        assert ad.title == "Alt Name Product"
        assert ad.advertiser == "AltShop"
        assert ad.landing_page == "https://altshop.com"
        assert ad.thumbnail_url == "https://img.com/cover.jpg"


class TestGetPiPiAdsAdapterForUser:
    @patch.dict("os.environ", {"APP_SECRET_KEY": ""})
    def test_missing_app_secret(self):
        result = get_pipiads_adapter_for_user("12345", MagicMock(), app_secret="")
        assert result is None

    @patch("db.service.get_user_integration_encrypted_secret", return_value=None)
    def test_no_saved_key(self, mock_get):
        result = get_pipiads_adapter_for_user(
            "12345", MagicMock(), app_secret="test_secret_key_1234567890"
        )
        assert result is None

    @patch("agent.secrets.open_secret", return_value="real_pipiads_key")
    @patch("db.service.get_user_integration_encrypted_secret", return_value="da1.blob")
    def test_success(self, mock_get, mock_open):
        result = get_pipiads_adapter_for_user(
            "12345", MagicMock(), app_secret="test_secret_key_1234567890"
        )
        assert result is not None
        assert isinstance(result, PiPiAdsAdapter)
        assert result._api_key == "real_pipiads_key"

    @patch("agent.secrets.open_secret", side_effect=Exception("decrypt error"))
    @patch("db.service.get_user_integration_encrypted_secret", return_value="da1.bad")
    def test_decrypt_failure(self, mock_get, mock_open):
        result = get_pipiads_adapter_for_user(
            "12345", MagicMock(), app_secret="test_secret_key_1234567890"
        )
        assert result is None
