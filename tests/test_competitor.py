"""Tests for competitor tracking logic."""

import asyncio
from datetime import datetime, timezone

from agent.competitor import CompetitorTracker
from agent.scanner import ScanResult, SoldItem


class FakeEbayScanner:
    def __init__(self, items):
        self.items = items
        self.calls = []

    async def search_sold(self, query, seller=None, limit=50, **kwargs):
        del kwargs
        self.calls.append((query, seller, limit))
        return ScanResult(query=query, items=self.items, total_found=len(self.items))


class TestCompetitorTracker:
    def test_scan_seller_marks_new_items(self):
        items = [
            SoldItem(
                title="AirPods Pro 2",
                sold_price=120.0,
                currency="USD",
                sold_date=datetime(2026, 4, 9, 8, 0, tzinfo=timezone.utc),
                condition="New",
                item_id="A1",
                seller="seller123",
                category="Headphones",
            ),
            SoldItem(
                title="Gaming Mouse",
                sold_price=45.0,
                currency="USD",
                sold_date=datetime(2026, 4, 9, 7, 0, tzinfo=timezone.utc),
                condition="New",
                item_id="B2",
                seller="seller123",
                category="PC",
            ),
        ]
        tracker = CompetitorTracker(FakeEbayScanner(items))

        report = asyncio.run(
            tracker.scan_seller("seller123", known_item_ids={"A1"}, query="electronics", limit=10)
        )

        assert report.seller_username == "seller123"
        assert report.new_count == 1
        assert report.items[1].is_new is True
        assert "COMPETITOR TRACKER" in report.summary()
