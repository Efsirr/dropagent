"""Tests for the CJDropshipping source integration."""

from datetime import datetime, timezone

from agent.sources.cj import CJDropshippingSource


SEARCH_RESPONSE = {
    "code": 200,
    "result": True,
    "message": "Success",
    "data": {
        "content": [
            {
                "productList": [
                    {
                        "id": "CJ-1001",
                        "nameEn": "LED Galaxy Projector",
                        "bigImage": "https://img.example.com/cj-1.jpg",
                        "sellPrice": "18.99",
                        "supplierName": "CJ Lighting",
                        "warehouseInventoryNum": 24,
                        "deliveryCycle": "8",
                        "currency": "USD",
                        "listedNum": 56,
                    }
                ]
            }
        ]
    },
}

DETAIL_RESPONSE = {
    "code": 200,
    "result": True,
    "message": "Success",
    "data": {
        "pid": "CJ-2002",
        "productNameEn": "Portable Blender Bottle",
        "productImage": "https://img.example.com/cj-2.jpg",
        "sellPrice": 12.5,
        "categoryName": "Home & Garden / Kitchen",
        "supplierName": "Blend Factory",
        "deliveryTime": "48",
        "listedNum": 12,
        "countryCode": "CN",
        "totalVerifiedInventory": 4,
    },
}


class TestCJDropshippingSource:
    def test_missing_api_key_raises(self):
        source = CJDropshippingSource(api_key="")

        try:
            import asyncio

            asyncio.run(source.search("projector"))
        except ValueError as error:
            assert "CJ_API_KEY" in str(error)
        else:
            raise AssertionError("Expected ValueError")

    def test_parse_expiry_handles_offset(self):
        parsed = CJDropshippingSource._parse_expiry("2021-08-18T09:16:33+08:00")

        assert parsed == datetime(2021, 8, 18, 1, 16, 33, tzinfo=timezone.utc)

    def test_parse_search_response_returns_products(self):
        source = CJDropshippingSource(api_key="test")

        products = source._parse_search_response(SEARCH_RESPONSE)

        assert len(products) == 1
        product = products[0]
        assert product.source == "cj"
        assert product.source_id == "CJ-1001"
        assert product.title == "LED Galaxy Projector"
        assert product.price == 18.99
        assert product.seller == "CJ Lighting"
        assert product.stock_status.value == "in_stock"
        assert product.estimated_delivery_days == 8
        assert product.review_count == 56

    def test_parse_detail_response_returns_product(self):
        source = CJDropshippingSource(api_key="test")

        product = source._parse_detail_response(DETAIL_RESPONSE)

        assert product is not None
        assert product.source_id == "CJ-2002"
        assert product.title == "Portable Blender Bottle"
        assert product.category == "Home & Garden / Kitchen"
        assert product.stock_status.value == "low_stock"
        assert product.estimated_delivery_days == 2
