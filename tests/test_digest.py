"""Tests for the daily digest generator."""

from datetime import datetime

from agent.analyzer import BusinessModel, calculate_margin
from agent.comparator import Opportunity
from agent.digest import DailyDigest, build_daily_digest
from agent.sources.base import ProductCondition, SourceProduct, StockStatus


def make_opportunity(
    source_id: str,
    title: str,
    price: float,
    shipping_cost: float,
    ebay_avg_price: float,
    ebay_sold_count: int,
) -> Opportunity:
    product = SourceProduct(
        source="amazon",
        source_id=source_id,
        url=f"https://example.com/{source_id}",
        title=title,
        price=price,
        currency="USD",
        condition=ProductCondition.NEW,
        stock_status=StockStatus.IN_STOCK,
        shipping_cost=shipping_cost,
    )
    margin = calculate_margin(
        buy_price=product.price,
        sell_price=ebay_avg_price,
        shipping_cost=product.shipping_cost,
        business_model=BusinessModel.US_ARBITRAGE,
        platform="ebay",
    )
    return Opportunity(
        source_product=product,
        ebay_avg_price=ebay_avg_price,
        ebay_sold_count=ebay_sold_count,
        margin=margin,
    )


class TestBuildDailyDigest:
    def test_build_daily_digest_sorts_by_score(self):
        low = make_opportunity("1", "Lower Profit Item", 40.0, 0.0, 70.0, 3)
        high = make_opportunity("2", "High Profit Item", 20.0, 0.0, 70.0, 3)

        digest = build_daily_digest(
            [low, high],
            generated_at=datetime(2026, 4, 9, 9, 0),
        )

        assert digest.count == 2
        assert digest.items[0].opportunity.source_product.source_id == "2"
        assert digest.items[1].opportunity.source_product.source_id == "1"

    def test_build_daily_digest_applies_filters_and_limit(self):
        opportunities = [
            make_opportunity("1", "Good Item", 20.0, 0.0, 80.0, 5),
            make_opportunity("2", "Too Small", 60.0, 0.0, 70.0, 5),
            make_opportunity("3", "Another Good Item", 25.0, 0.0, 85.0, 5),
        ]

        digest = build_daily_digest(
            opportunities,
            top_n=1,
            min_profit=20.0,
            generated_at=datetime(2026, 4, 9, 9, 0),
        )

        assert digest.count == 1
        assert digest.items[0].opportunity.margin.net_profit >= 20.0

    def test_digest_summary_contains_key_metrics(self):
        digest = build_daily_digest(
            [
                make_opportunity("1", "AirPods Pro 2", 50.0, 5.0, 110.0, 9),
                make_opportunity("2", "Gaming Mouse", 18.0, 0.0, 49.0, 4),
            ],
            title="US Retail Arbitrage",
            generated_at=datetime(2026, 4, 9, 9, 0),
        )

        summary = digest.summary()

        assert "DAILY MORNING DIGEST" in summary
        assert "US Retail Arbitrage" in summary
        assert "Average Profit" in summary
        assert "AirPods Pro 2" in summary

    def test_digest_summary_empty(self):
        digest = DailyDigest(
            title="Empty Report",
            generated_at=datetime(2026, 4, 9, 9, 0),
            items=[],
        )

        summary = digest.summary()
        assert "No profitable opportunities found" in summary

    def test_digest_summary_russian(self):
        digest = build_daily_digest(
            [make_opportunity("1", "Test Item", 20.0, 0.0, 80.0, 5)],
            generated_at=datetime(2026, 4, 9, 9, 0),
        )

        summary = digest.summary(lang="ru")

        assert "УТРЕННЯЯ СВОДКА" in summary
        assert "Средняя прибыль" in summary

    def test_to_dict_contains_expected_fields(self):
        digest = build_daily_digest(
            [make_opportunity("1", "Test Item", 20.0, 0.0, 80.0, 5)],
            generated_at=datetime(2026, 4, 9, 9, 0),
        )

        data = digest.to_dict()

        assert data["title"] == "Daily Opportunity Digest"
        assert data["count"] == 1
        assert "avg_profit" in data
        assert len(data["items"]) == 1
