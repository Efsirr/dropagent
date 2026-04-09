"""
AliExpress affiliate source integration.

Uses the AliExpress Open Platform affiliate APIs so Model 2 users can
search China-based products with the same SourceProduct contract used by
Amazon and Walmart.
"""

from __future__ import annotations

import hashlib
import os
import re
from typing import Any, Optional

import httpx

from agent.sources.base import (
    BaseSource,
    ProductCondition,
    SourceProduct,
    StockStatus,
)


ALIEXPRESS_GATEWAY_URL = "https://gw.api.taobao.com/router/rest"
DEFAULT_DETAIL_FIELDS = ",".join(
    [
        "product_id",
        "product_title",
        "promotion_link",
        "product_detail_url",
        "target_sale_price",
        "target_original_price",
        "sale_price",
        "original_price",
        "product_main_image_url",
        "first_level_category_name",
        "second_level_category_name",
        "product_shop_name",
        "shop_name",
        "evaluate_rate",
        "volume",
        "orders_count",
        "delivery_time",
        "ship_to_days",
        "shipping_fee",
        "freight_fee",
    ]
)

_PRICE_RE = re.compile(r"-?\d+(?:\.\d+)?")
_DAY_RE = re.compile(r"\d+")


class AliExpressSource(BaseSource):
    """AliExpress Open Platform affiliate client."""

    def __init__(
        self,
        app_key: Optional[str] = None,
        app_secret: Optional[str] = None,
        tracking_id: Optional[str] = None,
        country: str = "US",
        target_currency: str = "USD",
        target_language: str = "EN",
        timeout: float = 10.0,
    ):
        self._app_key = app_key or os.getenv("ALIEXPRESS_APP_KEY", "")
        self._app_secret = app_secret or os.getenv("ALIEXPRESS_APP_SECRET", "")
        self._tracking_id = tracking_id or os.getenv("ALIEXPRESS_TRACKING_ID", "")
        self._country = country
        self._target_currency = target_currency
        self._target_language = target_language
        self._timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def name(self) -> str:
        return "aliexpress"

    def _validate_credentials(self):
        if not self._app_key:
            raise ValueError("ALIEXPRESS_APP_KEY is required")
        if not self._app_secret:
            raise ValueError("ALIEXPRESS_APP_SECRET is required")

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self._timeout)
        return self._client

    def _sign_params(self, params: dict[str, Any]) -> str:
        """TOP signature: secret + sorted key/value pairs + secret, uppercase MD5."""
        payload = "".join(
            f"{key}{params[key]}"
            for key in sorted(params)
            if params[key] is not None and params[key] != ""
        )
        signed = f"{self._app_secret}{payload}{self._app_secret}"
        return hashlib.md5(signed.encode("utf-8")).hexdigest().upper()

    def _build_request_params(
        self,
        method: str,
        extra: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "method": method,
            "app_key": self._app_key,
            "sign_method": "md5",
            "format": "json",
            "v": "2.0",
            "target_currency": self._target_currency,
            "target_language": self._target_language,
            "country": self._country,
        }
        if self._tracking_id:
            params["tracking_id"] = self._tracking_id
        for key, value in (extra or {}).items():
            if value is not None and value != "":
                params[key] = value
        params["sign"] = self._sign_params(params)
        return params

    async def search(
        self,
        query: str,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 20,
    ) -> list[SourceProduct]:
        self._validate_credentials()
        params = self._build_request_params(
            "aliexpress.affiliate.product.query",
            {
                "keywords": query,
                "page_size": min(max(limit, 1), 50),
                "page_no": 1,
                "category_ids": category,
                "min_sale_price": f"{min_price:.2f}" if min_price is not None else None,
                "max_sale_price": f"{max_price:.2f}" if max_price is not None else None,
            },
        )

        client = await self._get_client()
        try:
            response = await client.get(ALIEXPRESS_GATEWAY_URL, params=params)
            response.raise_for_status()
            return self._parse_search_response(response.json())
        except httpx.HTTPStatusError as error:
            if error.response.status_code == 429:
                return []
            raise

    async def get_product(self, product_id: str) -> Optional[SourceProduct]:
        self._validate_credentials()
        params = self._build_request_params(
            "aliexpress.affiliate.productdetail.get",
            {
                "product_ids": product_id,
                "fields": DEFAULT_DETAIL_FIELDS,
            },
        )

        client = await self._get_client()
        try:
            response = await client.get(ALIEXPRESS_GATEWAY_URL, params=params)
            response.raise_for_status()
            products = self._parse_detail_response(response.json())
            return products[0] if products else None
        except httpx.HTTPStatusError as error:
            if error.response.status_code in (404, 429):
                return None
            raise

    def _extract_result(self, data: dict[str, Any]) -> dict[str, Any]:
        error = data.get("error_response")
        if isinstance(error, dict):
            raise ValueError(error.get("sub_msg") or error.get("msg") or "AliExpress API error")

        response_key = next((key for key in data if key.endswith("_response")), None)
        if response_key is None:
            return {}

        response_payload = data.get(response_key, {})
        resp_result = response_payload.get("resp_result", {})
        resp_code = resp_result.get("resp_code")
        if resp_code not in (None, 200, "200"):
            raise ValueError(resp_result.get("resp_msg", "AliExpress API error"))
        return resp_result.get("result", {}) or {}

    def _extract_products(self, result: dict[str, Any]) -> list[dict[str, Any]]:
        raw_products: Any = result.get("products") or result.get("items") or []
        if isinstance(raw_products, dict):
            raw_products = raw_products.get("product", raw_products.get("item", raw_products))
        if isinstance(raw_products, dict):
            return [raw_products]
        if isinstance(raw_products, list):
            return [item for item in raw_products if isinstance(item, dict)]
        return []

    def _parse_search_response(self, data: dict[str, Any]) -> list[SourceProduct]:
        return self._parse_products(self._extract_products(self._extract_result(data)))

    def _parse_detail_response(self, data: dict[str, Any]) -> list[SourceProduct]:
        return self._parse_products(self._extract_products(self._extract_result(data)))

    def _parse_products(self, products: list[dict[str, Any]]) -> list[SourceProduct]:
        parsed: list[SourceProduct] = []
        for item in products:
            product = self._parse_item(item)
            if product is not None:
                parsed.append(product)
        return parsed

    def _parse_item(self, item: dict[str, Any]) -> Optional[SourceProduct]:
        product_id = str(item.get("product_id") or item.get("item_id") or "").strip()
        if not product_id:
            return None

        price = self._parse_price(
            item.get("target_sale_price")
            or item.get("sale_price")
            or item.get("target_original_price")
            or item.get("original_price")
        )
        if price is None or price <= 0:
            return None

        shipping_cost = self._parse_price(item.get("shipping_fee") or item.get("freight_fee")) or 0.0
        delivery_days = self._parse_delivery_days(item.get("delivery_time") or item.get("ship_to_days"))
        category = " / ".join(
            part
            for part in (
                item.get("first_level_category_name"),
                item.get("second_level_category_name"),
            )
            if part
        ) or None
        url = (
            item.get("promotion_link")
            or item.get("product_detail_url")
            or f"https://www.aliexpress.com/item/{product_id}.html"
        )

        return SourceProduct(
            source="aliexpress",
            source_id=product_id,
            url=url,
            title=item.get("product_title") or item.get("title") or "Unknown Product",
            price=round(price, 2),
            currency=self._target_currency,
            condition=ProductCondition.NEW,
            category=category,
            brand=item.get("brand_name"),
            image_url=item.get("product_main_image_url") or item.get("image_url"),
            stock_status=StockStatus.IN_STOCK,
            seller=item.get("product_shop_name") or item.get("shop_name"),
            ships_from=(item.get("ship_from_country") or "CN").upper(),
            shipping_cost=round(shipping_cost, 2),
            estimated_delivery_days=delivery_days,
            rating=self._parse_price(item.get("evaluate_rate")),
            review_count=self._parse_int(item.get("orders_count") or item.get("volume")),
        )

    @staticmethod
    def _parse_price(value: Any) -> Optional[float]:
        if value is None or value == "":
            return None
        if isinstance(value, (int, float)):
            return float(value)
        match = _PRICE_RE.search(str(value).replace(",", ""))
        if not match:
            return None
        return float(match.group(0))

    @staticmethod
    def _parse_int(value: Any) -> Optional[int]:
        number = AliExpressSource._parse_price(value)
        if number is None:
            return None
        return int(number)

    @staticmethod
    def _parse_delivery_days(value: Any) -> Optional[int]:
        if value is None or value == "":
            return None
        if isinstance(value, (int, float)):
            return int(value)
        days = [int(match) for match in _DAY_RE.findall(str(value))]
        if not days:
            return None
        return max(days)

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
