"""Tests for the AliExpress source integration."""

from agent.sources.aliexpress import AliExpressSource


SAMPLE_SEARCH_RESPONSE = {
    "aliexpress_affiliate_product_query_response": {
        "resp_result": {
            "resp_code": 200,
            "resp_msg": "success",
            "result": {
                "products": {
                    "product": [
                        {
                            "product_id": "1005001001",
                            "product_title": "Magnetic Wireless Charger",
                            "promotion_link": "https://s.click.aliexpress.com/test-1",
                            "target_sale_price": "US $12.49",
                            "shipping_fee": "US $1.99",
                            "first_level_category_name": "Consumer Electronics",
                            "second_level_category_name": "Chargers",
                            "product_main_image_url": "https://img.example.com/1.jpg",
                            "product_shop_name": "Top Charger Store",
                            "evaluate_rate": "4.8",
                            "volume": "321",
                            "delivery_time": "7-10 days",
                            "ship_from_country": "CN",
                        },
                        {
                            "product_id": "1005001002",
                            "product_title": "Item without price",
                        },
                    ]
                }
            },
        }
    }
}

SAMPLE_DETAIL_RESPONSE = {
    "aliexpress_affiliate_productdetail_get_response": {
        "resp_result": {
            "resp_code": 200,
            "resp_msg": "success",
            "result": {
                "products": {
                    "product": [
                        {
                            "product_id": "1005002001",
                            "product_title": "Anime Desk Lamp",
                            "product_detail_url": "https://www.aliexpress.com/item/1005002001.html",
                            "target_sale_price": "24.00",
                            "freight_fee": "0.00",
                            "first_level_category_name": "Lights",
                            "shop_name": "Lamp Hub",
                            "orders_count": "87",
                            "ship_to_days": "12",
                        }
                    ]
                }
            },
        }
    }
}


class TestAliExpressSource:
    def test_missing_credentials_raise(self):
        source = AliExpressSource(app_key="", app_secret="")

        try:
            import asyncio

            asyncio.run(source.search("desk lamp"))
        except ValueError as error:
            assert "ALIEXPRESS_APP_KEY" in str(error)
        else:
            raise AssertionError("Expected ValueError")

    def test_sign_params_matches_top_style_md5(self):
        source = AliExpressSource(app_key="test", app_secret="secret")

        sign = source._sign_params(
            {
                "method": "aliexpress.affiliate.product.query",
                "app_key": "test",
                "format": "json",
                "v": "2.0",
                "sign_method": "md5",
                "keywords": "desk lamp",
            }
        )

        assert sign == "7A61A32CC3AAD63DCEFF035B3C87007E"

    def test_parse_search_response_returns_source_products(self):
        source = AliExpressSource(app_key="key", app_secret="secret")

        products = source._parse_search_response(SAMPLE_SEARCH_RESPONSE)

        assert len(products) == 1
        product = products[0]
        assert product.source == "aliexpress"
        assert product.source_id == "1005001001"
        assert product.title == "Magnetic Wireless Charger"
        assert product.price == 12.49
        assert product.shipping_cost == 1.99
        assert product.category == "Consumer Electronics / Chargers"
        assert product.seller == "Top Charger Store"
        assert product.review_count == 321
        assert product.estimated_delivery_days == 10
        assert product.ships_from == "CN"

    def test_parse_detail_response_returns_product(self):
        source = AliExpressSource(app_key="key", app_secret="secret")

        products = source._parse_detail_response(SAMPLE_DETAIL_RESPONSE)

        assert len(products) == 1
        product = products[0]
        assert product.source_id == "1005002001"
        assert product.price == 24.0
        assert product.shipping_cost == 0.0
        assert product.seller == "Lamp Hub"
        assert product.review_count == 87
        assert product.estimated_delivery_days == 12
