"""Tests for the price comparison engine."""

import asyncio
from typing import Optional

from agent.comparator import KeepaInsight, PriceComparator
from agent.scanner import ScanResult, SoldItem
from agent.sources.base import BaseSource, ProductCondition, SourceProduct, StockStatus


class FakeSource(BaseSource):
    """Simple in-memory source for comparator tests."""

    def __init__(self, products: list[SourceProduct]):
        self._products = products

    @property
    def name(self) -> str:
        return "fake"

    async def search(
        self,
        query: str,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 20,
    ) -> list[SourceProduct]:
        del query, category, min_price
        products = self._products
        if max_price is not None:
            products = [product for product in products if product.price <= max_price]
        return products[:limit]

    async def get_product(self, product_id: str) -> Optional[SourceProduct]:
        for product in self._products:
            if product.source_id == product_id:
                return product
        return None


class FakeScanner:
    """Simple in-memory eBay scanner for comparator tests."""

    def __init__(self, result: ScanResult):
        self._result = result
        self.queries: list[str] = []

    async def search_sold(self, query: str, limit: int = 50) -> ScanResult:
        del limit
        self.queries.append(query)
        return self._result

    async def close(self):
        return None


class FakeKeepaProduct:
    def __init__(self, price_90d_avg=84.5, current_amazon_price=72.0):
        self.current_amazon_price = current_amazon_price
        self.price_30d_avg = 79.0
        self.price_90d_avg = price_90d_avg
        self.price_30d_min = 69.0
        self.price_30d_max = 89.0
        self.price_drops_90d = 2


class FakeKeepaAdapter:
    def __init__(self, results: dict[str, FakeKeepaProduct]):
        self.results = results
        self.calls = []

    async def get_products(self, asins: list[str]):
        self.calls.append(asins)
        return [self.results.get(asin) for asin in asins]

    async def close(self):
        return None


def make_product(
    source_id: str,
    title: str,
    price: float,
    shipping_cost: float = 0.0,
) -> SourceProduct:
    return SourceProduct(
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


def make_scan_result(avg_prices: list[float]) -> ScanResult:
    items = [
        SoldItem(
            title=f"Sold Item {idx}",
            sold_price=price,
            currency="USD",
            sold_date=None,
            condition="New",
            item_id=str(idx),
        )
        for idx, price in enumerate(avg_prices, start=1)
    ]
    return ScanResult(query="airpods", items=items, total_found=len(items))


class TestPriceComparator:
    def test_find_opportunities_uses_single_shipping_charge(self):
        product = make_product("sku-1", "AirPods Pro", price=50.0, shipping_cost=5.0)
        scanner = FakeScanner(make_scan_result([100.0, 100.0, 100.0]))
        comparator = PriceComparator(
            sources=[FakeSource([product])],
            ebay_scanner=scanner,
            min_profit=0.0,
            min_sold_count=1,
        )

        results = asyncio.run(comparator.find_opportunities("airpods"))

        assert len(results) == 1
        opportunity = results[0]
        assert opportunity.margin.shipping_cost == 5.0
        assert opportunity.margin.total_cost == 72.7
        assert opportunity.margin.net_profit == 27.3

    def test_find_opportunities_sorts_by_score(self):
        cheap = make_product("sku-1", "Budget Item", price=30.0, shipping_cost=0.0)
        expensive = make_product("sku-2", "Premium Item", price=60.0, shipping_cost=0.0)
        scanner = FakeScanner(make_scan_result([100.0, 100.0, 100.0, 100.0]))
        comparator = PriceComparator(
            sources=[FakeSource([expensive, cheap])],
            ebay_scanner=scanner,
            min_profit=0.0,
            min_sold_count=1,
        )

        results = asyncio.run(comparator.find_opportunities("test"))

        assert len(results) == 2
        assert results[0].source_product.source_id == "sku-1"
        assert results[0].score > results[1].score

    def test_find_opportunities_filters_low_demand(self):
        product = make_product("sku-1", "Slow Seller", price=20.0)
        scanner = FakeScanner(make_scan_result([50.0]))
        comparator = PriceComparator(
            sources=[FakeSource([product])],
            ebay_scanner=scanner,
            min_profit=0.0,
            min_sold_count=2,
        )

        results = asyncio.run(comparator.find_opportunities("slow seller"))

        assert results == []

    def test_compare_product_uses_custom_query(self):
        product = make_product("sku-1", "Source Title", price=40.0, shipping_cost=3.0)
        scanner = FakeScanner(make_scan_result([90.0, 90.0, 90.0]))
        comparator = PriceComparator(
            sources=[],
            ebay_scanner=scanner,
            min_profit=0.0,
            min_sold_count=1,
        )

        result = asyncio.run(
            comparator.compare_product(product, ebay_query="custom ebay query")
        )

        assert result is not None
        assert scanner.queries == ["custom ebay query"]
        assert result.margin.total_cost == 59.11
        assert result.margin.net_profit == 30.89

    def test_find_opportunities_adds_keepa_insight_for_amazon_products(self):
        product = make_product("B09TEST123", "AirPods Pro", price=50.0, shipping_cost=5.0)
        scanner = FakeScanner(make_scan_result([100.0, 100.0, 100.0]))
        keepa = FakeKeepaAdapter({"B09TEST123": FakeKeepaProduct()})
        comparator = PriceComparator(
            sources=[FakeSource([product])],
            ebay_scanner=scanner,
            min_profit=0.0,
            min_sold_count=1,
            keepa_adapter=keepa,
        )

        results = asyncio.run(comparator.find_opportunities("airpods"))

        assert len(results) == 1
        insight = results[0].keepa_insight
        assert isinstance(insight, KeepaInsight)
        assert insight is not None
        assert insight.asin == "B09TEST123"
        assert insight.avg_90d == 84.5
        assert keepa.calls == [["B09TEST123"]]
