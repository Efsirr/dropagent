"""Tests for StoreLeads discovery report formatting."""

from datetime import datetime, timezone

from agent.adapters.storeleads import StoreDomain
from agent.store_discovery import build_store_discovery_report


class TestStoreDiscoveryReport:
    def test_summary_contains_store_metrics(self):
        report = build_store_discovery_report(
            query="pet accessories",
            platform="shopify",
            generated_at=datetime(2026, 4, 9, 10, 0, tzinfo=timezone.utc),
            stores=[
                StoreDomain(
                    domain="petjoy.example",
                    merchant_name="Pet Joy",
                    estimated_visits=120000,
                    estimated_sales_monthly_usd=54000.0,
                    avg_price_usd=31.5,
                )
            ],
        )

        summary = report.summary()

        assert "STORE DISCOVERY" in summary
        assert "pet accessories" in summary
        assert "Pet Joy" in summary
        assert "Visits 120000" in summary

    def test_summary_empty(self):
        report = build_store_discovery_report(
            query="desk toys",
            stores=[],
        )

        summary = report.summary()

        assert "No competitor stores found" in summary
