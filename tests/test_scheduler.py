"""Tests for digest scheduling orchestration."""

import asyncio
from datetime import datetime

from agent.analyzer import BusinessModel, calculate_margin
from agent.comparator import Opportunity
from agent.scheduler import MorningDigestScheduler, ScanRequest, load_scan_requests_from_env
from agent.sources.base import ProductCondition, SourceProduct, StockStatus


def make_opportunity(
    source_id: str,
    title: str,
    price: float,
    ebay_avg_price: float,
    ebay_sold_count: int,
    shipping_cost: float = 0.0,
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
        shipping_cost=shipping_cost,
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
    def __init__(self, results_by_query: dict[str, list[Opportunity]]):
        self.results_by_query = results_by_query
        self.calls = []

    async def find_opportunities(
        self,
        query: str,
        category=None,
        max_buy_price=None,
        limit: int = 20,
    ) -> list[Opportunity]:
        self.calls.append(
            {
                "query": query,
                "category": category,
                "max_buy_price": max_buy_price,
                "limit": limit,
            }
        )
        return self.results_by_query.get(query, [])


class TestLoadScanRequestsFromEnv:
    def test_loads_comma_separated_queries(self):
        requests = load_scan_requests_from_env(
            {"DIGEST_QUERIES": "airpods pro, gaming mouse, lego star wars"}
        )

        assert [request.query for request in requests] == [
            "airpods pro",
            "gaming mouse",
            "lego star wars",
        ]

    def test_ignores_blank_entries(self):
        requests = load_scan_requests_from_env({"DIGEST_QUERIES": " , airpods , , "})

        assert [request.query for request in requests] == ["airpods"]


class TestMorningDigestScheduler:
    def test_generate_digest_combines_queries(self):
        comparator = FakeComparator(
            {
                "airpods": [make_opportunity("1", "AirPods", 40.0, 90.0, 5)],
                "mouse": [make_opportunity("2", "Gaming Mouse", 20.0, 60.0, 4)],
            }
        )
        scheduler = MorningDigestScheduler(comparator, top_n=5, min_profit=0.0)

        digest = asyncio.run(
            scheduler.generate_digest(
                [
                    ScanRequest(query="airpods"),
                    ScanRequest(query="mouse"),
                ],
                generated_at=datetime(2026, 4, 9, 9, 0),
            )
        )

        assert digest.count == 2
        assert len(comparator.calls) == 2
        assert digest.items[0].opportunity.score >= digest.items[1].opportunity.score

    def test_generate_digest_deduplicates_same_product(self):
        duplicate_low = make_opportunity("1", "AirPods", 50.0, 90.0, 3)
        duplicate_high = make_opportunity("1", "AirPods", 40.0, 90.0, 6)
        comparator = FakeComparator(
            {
                "airpods": [duplicate_low],
                "airpods pro": [duplicate_high],
            }
        )
        scheduler = MorningDigestScheduler(comparator, top_n=5, min_profit=0.0)

        digest = asyncio.run(
            scheduler.generate_digest(
                [
                    ScanRequest(query="airpods"),
                    ScanRequest(query="airpods pro"),
                ],
                generated_at=datetime(2026, 4, 9, 9, 0),
            )
        )

        assert digest.count == 1
        assert digest.items[0].opportunity.margin.net_profit == duplicate_high.margin.net_profit

    def test_generate_digest_empty_requests(self):
        scheduler = MorningDigestScheduler(FakeComparator({}))

        digest = asyncio.run(
            scheduler.generate_digest([], generated_at=datetime(2026, 4, 9, 9, 0))
        )

        assert digest.count == 0
        assert digest.title == "Daily Opportunity Digest"

    def test_generate_digest_passes_request_filters(self):
        comparator = FakeComparator({"airpods": []})
        scheduler = MorningDigestScheduler(comparator)

        asyncio.run(
            scheduler.generate_digest(
                [
                    ScanRequest(
                        query="airpods",
                        category="electronics",
                        max_buy_price=75.0,
                        limit=10,
                    )
                ],
                generated_at=datetime(2026, 4, 9, 9, 0),
            )
        )

        assert comparator.calls == [
            {
                "query": "airpods",
                "category": "electronics",
                "max_buy_price": 75.0,
                "limit": 10,
            }
        ]
