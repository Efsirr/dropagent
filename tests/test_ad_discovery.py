"""Tests for PiPiADS ad discovery report formatting."""

from datetime import datetime, timezone

from agent.ad_discovery import build_ad_discovery_report
from agent.adapters.pipiads import TikTokAd


class TestAdDiscoveryReport:
    def test_summary_contains_ad_metrics(self):
        report = build_ad_discovery_report(
            query="pet hair remover",
            generated_at=datetime(2026, 4, 10, 10, 0, tzinfo=timezone.utc),
            ads=[
                TikTokAd(
                    ad_id="1",
                    title="Pet Hair Remover Roller",
                    advertiser="PetHero",
                    total_likes=12000,
                    total_shares=2100,
                    days_running=7,
                    trend_score=5432.1,
                )
            ],
        )

        summary = report.summary()

        assert "AD DISCOVERY" in summary
        assert "pet hair remover" in summary
        assert "PetHero" in summary
        assert "Likes 12000" in summary

    def test_summary_empty(self):
        report = build_ad_discovery_report(
            query="desk lamp",
            ads=[],
        )

        summary = report.summary()

        assert "No trending ads found" in summary
