"""Tests for the eBay sold listings scanner."""

import pytest
from datetime import datetime

from agent.scanner import EbayScanner, ScanResult, SoldItem


# Sample Finding API response for testing
SAMPLE_FINDING_RESPONSE = {
    "findCompletedItemsResponse": [
        {
            "searchResult": [
                {
                    "@count": "3",
                    "item": [
                        {
                            "itemId": ["123456"],
                            "title": ["Apple AirPods Pro 2nd Generation"],
                            "sellingStatus": [
                                {
                                    "currentPrice": [
                                        {"__value__": "189.99", "@currencyId": "USD"}
                                    ]
                                }
                            ],
                            "listingInfo": [
                                {"endTime": ["2024-03-15T10:30:00Z"]}
                            ],
                            "condition": [
                                {"conditionDisplayName": ["New"]}
                            ],
                            "galleryURL": ["https://example.com/img1.jpg"],
                            "sellerInfo": [{"sellerUserName": ["seller123"]}],
                            "primaryCategory": [{"categoryName": ["Headphones"]}],
                        },
                        {
                            "itemId": ["789012"],
                            "title": ["AirPods Pro with MagSafe Case"],
                            "sellingStatus": [
                                {
                                    "currentPrice": [
                                        {"__value__": "165.00", "@currencyId": "USD"}
                                    ]
                                }
                            ],
                            "listingInfo": [
                                {"endTime": ["2024-03-14T08:00:00Z"]}
                            ],
                            "condition": [
                                {"conditionDisplayName": ["Used"]}
                            ],
                            "galleryURL": [None],
                            "sellerInfo": [{"sellerUserName": ["deals_hub"]}],
                            "primaryCategory": [{"categoryName": ["Headphones"]}],
                        },
                        {
                            "itemId": ["345678"],
                            "title": ["AirPods Pro - Sealed Box"],
                            "sellingStatus": [
                                {
                                    "currentPrice": [
                                        {"__value__": "210.50", "@currencyId": "USD"}
                                    ]
                                }
                            ],
                            "listingInfo": [
                                {"endTime": ["2024-03-13T15:00:00Z"]}
                            ],
                            "condition": [
                                {"conditionDisplayName": ["New"]}
                            ],
                            "galleryURL": ["https://example.com/img3.jpg"],
                            "sellerInfo": [{"sellerUserName": ["tech_store"]}],
                            "primaryCategory": [{"categoryName": ["Headphones"]}],
                        },
                    ],
                }
            ]
        }
    ]
}


class TestSoldItem:
    def test_to_dict(self):
        item = SoldItem(
            title="Test Product",
            sold_price=29.99,
            currency="USD",
            sold_date=datetime(2024, 3, 15),
            condition="New",
            item_id="12345",
        )
        d = item.to_dict()
        assert d["title"] == "Test Product"
        assert d["sold_price"] == 29.99
        assert d["item_id"] == "12345"


class TestScanResult:
    def _make_result(self) -> ScanResult:
        items = [
            SoldItem("Item A", 10.0, "USD", None, "New", "1"),
            SoldItem("Item B", 20.0, "USD", None, "Used", "2"),
            SoldItem("Item C", 30.0, "USD", None, "New", "3"),
        ]
        return ScanResult(query="test", items=items, total_found=3)

    def test_avg_price(self):
        result = self._make_result()
        assert result.avg_price == 20.0

    def test_min_max_price(self):
        result = self._make_result()
        assert result.min_price == 10.0
        assert result.max_price == 30.0

    def test_count(self):
        result = self._make_result()
        assert result.count == 3

    def test_empty_result(self):
        result = ScanResult(query="nothing", items=[], total_found=0)
        assert result.avg_price == 0.0
        assert result.min_price == 0.0
        assert result.max_price == 0.0
        assert result.count == 0

    def test_summary_output(self):
        result = self._make_result()
        summary = result.summary()
        assert "test" in summary
        assert "$20.00" in summary  # avg price

    def test_summary_empty(self):
        result = ScanResult(query="nothing", items=[], total_found=0)
        summary = result.summary()
        assert "No sold listings found" in summary

    def test_summary_russian(self):
        result = self._make_result()
        summary = result.summary(lang="ru")
        assert "ПРОДАННЫЕ ТОВАРЫ" in summary

    def test_to_dict(self):
        result = self._make_result()
        d = result.to_dict()
        assert d["query"] == "test"
        assert d["avg_price"] == 20.0
        assert len(d["items"]) == 3


class TestEbayScanner:
    def test_missing_api_key_raises(self):
        scanner = EbayScanner(app_id="")
        with pytest.raises(ValueError, match="EBAY_APP_ID"):
            import asyncio
            asyncio.run(scanner.search_sold("test"))

    def test_parse_finding_response(self):
        """Parse a real-shaped Finding API response."""
        scanner = EbayScanner(app_id="test")
        result = scanner._parse_finding_response("airpods pro", SAMPLE_FINDING_RESPONSE)

        assert result.query == "airpods pro"
        assert result.total_found == 3
        assert result.count == 3
        assert result.avg_price == pytest.approx(188.50, abs=0.01)

        # Check first item
        item = result.items[0]
        assert item.title == "Apple AirPods Pro 2nd Generation"
        assert item.sold_price == 189.99
        assert item.condition == "New"
        assert item.seller == "seller123"
        assert item.category == "Headphones"

    def test_parse_empty_response(self):
        scanner = EbayScanner(app_id="test")
        result = scanner._parse_finding_response("nope", {})
        assert result.count == 0
        assert result.total_found == 0

    def test_build_params_basic(self):
        scanner = EbayScanner(app_id="MY_KEY")
        params = scanner._build_finding_params("airpods", None, None, None, None, None, 50)

        assert params["keywords"] == "airpods"
        assert params["SECURITY-APPNAME"] == "MY_KEY"
        assert params["itemFilter(0).value"] == "true"  # SoldItemsOnly

    def test_build_params_with_filters(self):
        scanner = EbayScanner(app_id="MY_KEY")
        params = scanner._build_finding_params(
            "iphone", min_price=100, max_price=500, category_id="9355",
            condition="new", seller=None, limit=25
        )

        assert params["itemFilter(1).name"] == "MinPrice"
        assert params["itemFilter(1).value"] == "100"
        assert params["itemFilter(2).name"] == "MaxPrice"
        assert params["itemFilter(2).value"] == "500"
        assert params["categoryId"] == "9355"
        assert params["paginationInput.entriesPerPage"] == "25"

    def test_build_params_with_seller_filter(self):
        scanner = EbayScanner(app_id="MY_KEY")
        params = scanner._build_finding_params(
            "iphone", min_price=None, max_price=None, category_id=None,
            condition=None, seller="bestseller", limit=25
        )

        assert params["itemFilter(1).name"] == "Seller"
        assert params["itemFilter(1).value"] == "bestseller"
