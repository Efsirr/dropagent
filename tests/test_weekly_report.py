"""Tests for the weekly category report."""

import asyncio
from datetime import datetime, timezone

from agent.analyzer import BusinessModel, calculate_margin
from agent.comparator import Opportunity
from agent.sources.base import ProductCondition, SourceProduct, StockStatus
from agent.trends import RedditTrendResult, RedditTrendSignal, TrendKeyword, TrendScanResult
from agent.weekly_report import (
    WeeklyCategoryReporter,
    WeeklyCategoryReport,
    build_weekly_category_report,
    classify_trend_direction,
)


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
        category="electronics",
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


class FakeComparator:
    def __init__(self, mapping):
        self.mapping = mapping
        self.calls = []

    async def find_opportunities(self, query, category=None, max_buy_price=None, limit=20):
        del max_buy_price, limit
        self.calls.append((query, category))
        return list(self.mapping.get((query, category), []))


class FakeGoogleScanner:
    def __init__(self, results):
        self.results = results

    def scan_categories(self, categories, limit=5):
        del categories, limit
        return self.results


class FakeRedditScanner:
    def __init__(self, results):
        self.results = results

    def scan_categories(self, categories, limit=5):
        del categories, limit
        return self.results


class TestWeeklyHelpers:
    def test_classify_trend_direction_detects_rising_and_declining(self):
        assert classify_trend_direction(80, previous_score=40) == "rising"
        assert classify_trend_direction(10, previous_score=40) == "declining"
        assert classify_trend_direction(35, previous_score=30) == "stable"


class TestBuildWeeklyCategoryReport:
    def test_builds_sections_with_direction_and_keywords(self):
        opportunities = {
            "electronics": [
                make_opportunity("1", "AirPods Pro 2", 50.0, 0.0, 110.0, 9),
                make_opportunity("2", "Gaming Mouse", 18.0, 0.0, 49.0, 4),
            ],
            "toys": [],
        }
        google_results = [
            TrendScanResult(
                category="electronics",
                keywords=[TrendKeyword("airpods pro", 120, category="electronics")],
                generated_at=datetime(2026, 4, 9, 9, 0, tzinfo=timezone.utc),
            ),
            TrendScanResult(
                category="toys",
                keywords=[TrendKeyword("lego set", 18, category="toys")],
                generated_at=datetime(2026, 4, 9, 9, 0, tzinfo=timezone.utc),
            ),
        ]
        reddit_results = [
            RedditTrendResult(
                category="electronics",
                signals=[
                    RedditTrendSignal(
                        title="AirPods Pro deal",
                        subreddit="buildapcsales",
                        score=160.0,
                        url="https://example.com",
                    )
                ],
                generated_at=datetime(2026, 4, 9, 9, 0, tzinfo=timezone.utc),
            )
        ]

        report = build_weekly_category_report(
            category_opportunities=opportunities,
            google_results=google_results,
            reddit_results=reddit_results,
            generated_at=datetime(2026, 4, 9, 9, 0, tzinfo=timezone.utc),
        )

        assert isinstance(report, WeeklyCategoryReport)
        assert report.count == 2
        assert report.sections[0].category == "electronics"
        assert report.sections[0].trend_direction == "rising"
        assert report.sections[0].top_keywords == ["airpods pro"]
        assert "WEEKLY CATEGORY REPORT" in report.summary()

    def test_summary_renders_russian_labels(self):
        report = build_weekly_category_report(
            category_opportunities={
                "electronics": [make_opportunity("1", "AirPods Pro 2", 50.0, 0.0, 110.0, 9)]
            },
            google_results=[
                TrendScanResult(
                    category="electronics",
                    keywords=[TrendKeyword("airpods pro", 120, category="electronics")],
                    generated_at=datetime(2026, 4, 9, 9, 0, tzinfo=timezone.utc),
                )
            ],
            generated_at=datetime(2026, 4, 9, 9, 0, tzinfo=timezone.utc),
        )

        summary = report.summary(lang="ru")

        assert "ЕЖЕНЕДЕЛЬНЫЙ ОТЧЁТ ПО КАТЕГОРИЯМ" in summary
        assert "Средняя прибыль" in summary


class TestWeeklyCategoryReporter:
    def test_generate_report_combines_trends_and_opportunities(self):
        google_results = [
            TrendScanResult(
                category="electronics",
                keywords=[
                    TrendKeyword("airpods pro", 120, category="electronics"),
                    TrendKeyword("gaming mouse", 70, category="electronics"),
                ],
                generated_at=datetime(2026, 4, 9, 9, 0, tzinfo=timezone.utc),
            )
        ]
        reddit_results = [
            RedditTrendResult(
                category="electronics",
                signals=[
                    RedditTrendSignal(
                        title="AirPods Pro deal",
                        subreddit="buildapcsales",
                        score=140.0,
                        url="https://example.com",
                    )
                ],
                generated_at=datetime(2026, 4, 9, 9, 0, tzinfo=timezone.utc),
            )
        ]
        comparator = FakeComparator(
            {
                ("airpods pro", "electronics"): [
                    make_opportunity("1", "AirPods Pro 2", 50.0, 0.0, 110.0, 9)
                ],
                ("gaming mouse", "electronics"): [
                    make_opportunity("2", "Gaming Mouse", 18.0, 0.0, 49.0, 4)
                ],
            }
        )
        reporter = WeeklyCategoryReporter(
            comparator=comparator,
            google_scanner=FakeGoogleScanner(google_results),
            reddit_scanner=FakeRedditScanner(reddit_results),
            top_products=5,
            trend_limit=2,
            query_limit=10,
        )

        report = asyncio.run(reporter.generate_report(["electronics"]))

        assert report.sections[0].category == "electronics"
        assert report.sections[0].count == 2
        assert ("airpods pro", "electronics") in comparator.calls
        assert ("gaming mouse", "electronics") in comparator.calls
