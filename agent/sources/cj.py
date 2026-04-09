"""
CJDropshipping API v2 source integration.

Uses CJ's token-based API to search Model 2 products and map them into the
shared SourceProduct contract used by the rest of DropAgent.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import math
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


CJ_BASE_URL = "https://developers.cjdropshipping.com/api2.0/v1"
CJ_AUTH_URL = f"{CJ_BASE_URL}/authentication/getAccessToken"
CJ_PRODUCT_LIST_URL = f"{CJ_BASE_URL}/product/listV2"
CJ_PRODUCT_QUERY_URL = f"{CJ_BASE_URL}/product/query"
_NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?")


class CJDropshippingSource(BaseSource):
    """CJ API v2 client."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        country_code: str = "US",
        timeout: float = 10.0,
    ):
        self._api_key = api_key or os.getenv("CJ_API_KEY", "")
        self._country_code = country_code
        self._timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        self._access_token: Optional[str] = None
        self._access_token_expires_at: Optional[datetime] = None

    @property
    def name(self) -> str:
        return "cj"

    def _validate_credentials(self):
        if not self._api_key:
            raise ValueError("CJ_API_KEY is required")

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self._timeout)
        return self._client

    async def _ensure_access_token(self) -> str:
        self._validate_credentials()
        now = datetime.now(timezone.utc)
        if (
            self._access_token
            and self._access_token_expires_at
            and self._access_token_expires_at - timedelta(minutes=5) > now
        ):
            return self._access_token

        client = await self._get_client()
        response = await client.post(
            CJ_AUTH_URL,
            json={"apiKey": self._api_key},
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        data = response.json()
        self._ensure_success(data)
        payload = data.get("data") or {}
        token = payload.get("accessToken")
        if not token:
            raise ValueError("CJ access token missing from response")
        self._access_token = token
        expires_raw = payload.get("accessTokenExpiryDate")
        self._access_token_expires_at = self._parse_expiry(expires_raw) or (
            now + timedelta(days=14)
        )
        return token

    async def _request(self, url: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        token = await self._ensure_access_token()
        client = await self._get_client()
        response = await client.get(
            url,
            params=params,
            headers={"CJ-Access-Token": token},
        )
        response.raise_for_status()
        data = response.json()
        self._ensure_success(data)
        return data

    async def search(
        self,
        query: str,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 20,
    ) -> list[SourceProduct]:
        params = {
            "keyWord": query,
            "page": 1,
            "size": min(max(limit, 1), 100),
            "countryCode": self._country_code,
        }
        if category:
            params["categoryId"] = category
        if min_price is not None:
            params["startSellPrice"] = min_price
        if max_price is not None:
            params["endSellPrice"] = max_price

        try:
            data = await self._request(CJ_PRODUCT_LIST_URL, params=params)
            return self._parse_search_response(data)
        except httpx.HTTPStatusError as error:
            if error.response.status_code == 429:
                return []
            raise

    async def get_product(self, product_id: str) -> Optional[SourceProduct]:
        try:
            data = await self._request(
                CJ_PRODUCT_QUERY_URL,
                params={
                    "pid": product_id,
                    "countryCode": self._country_code,
                },
            )
            return self._parse_detail_response(data)
        except httpx.HTTPStatusError as error:
            if error.response.status_code in (404, 429):
                return None
            raise

    def _ensure_success(self, data: dict[str, Any]):
        code = data.get("code")
        result = data.get("result")
        if code not in (None, 200) or result is False:
            raise ValueError(data.get("message") or "CJ API error")

    def _parse_search_response(self, data: dict[str, Any]) -> list[SourceProduct]:
        payload = data.get("data") or {}
        products: list[dict[str, Any]] = []
        content = payload.get("content") or []
        for entry in content:
            products.extend(entry.get("productList") or [])
        products.extend(payload.get("list") or [])
        seen: set[str] = set()
        parsed: list[SourceProduct] = []
        for item in products:
            product = self._parse_item(item)
            if product is not None and product.source_id not in seen:
                parsed.append(product)
                seen.add(product.source_id)
        return parsed

    def _parse_detail_response(self, data: dict[str, Any]) -> Optional[SourceProduct]:
        payload = data.get("data") or {}
        return self._parse_item(payload)

    def _parse_item(self, item: dict[str, Any]) -> Optional[SourceProduct]:
        product_id = str(item.get("id") or item.get("pid") or "").strip()
        if not product_id:
            return None

        price = self._parse_float(item.get("sellPrice"))
        if price is None or price <= 0:
            return None

        inventory = (
            self._parse_float(item.get("warehouseInventoryNum"))
            or self._parse_float(item.get("totalVerifiedInventory"))
            or self._parse_float(item.get("totalInventoryNum"))
        )
        if inventory is not None and inventory <= 0:
            stock_status = StockStatus.OUT_OF_STOCK
        elif inventory is not None and inventory < 10:
            stock_status = StockStatus.LOW_STOCK
        else:
            stock_status = StockStatus.IN_STOCK

        shipping_cost = 0.0 if item.get("addMarkStatus") == 1 or item.get("isFreeShipping") is True else 0.0
        delivery_days = self._parse_delivery_days(item.get("deliveryCycle") or item.get("deliveryTime"))
        image = item.get("bigImage") or item.get("productImage")
        title = item.get("nameEn") or item.get("productNameEn") or item.get("en")
        url = f"https://app.cjdropshipping.com/product-detail.html?pid={product_id}"

        return SourceProduct(
            source="cj",
            source_id=product_id,
            url=url,
            title=title or "Unknown Product",
            price=round(price, 2),
            currency=item.get("currency") or "USD",
            condition=ProductCondition.NEW,
            category=item.get("categoryName"),
            brand=None,
            image_url=image,
            stock_status=stock_status,
            seller=item.get("supplierName"),
            ships_from=(item.get("countryCode") or self._country_code or "CN").upper(),
            shipping_cost=round(shipping_cost, 2),
            estimated_delivery_days=delivery_days,
            rating=None,
            review_count=self._parse_int(item.get("listedNum")),
        )

    @staticmethod
    def _parse_float(value: Any) -> Optional[float]:
        if value is None or value == "":
            return None
        if isinstance(value, (int, float)):
            return float(value)
        match = _NUMBER_RE.search(str(value).replace(",", ""))
        if not match:
            return None
        return float(match.group(0))

    @staticmethod
    def _parse_int(value: Any) -> Optional[int]:
        parsed = CJDropshippingSource._parse_float(value)
        if parsed is None:
            return None
        return int(parsed)

    @staticmethod
    def _parse_delivery_days(value: Any) -> Optional[int]:
        parsed = CJDropshippingSource._parse_float(value)
        if parsed is None:
            return None
        if parsed <= 14:
            return int(parsed)
        return max(1, math.ceil(parsed / 24))

    @staticmethod
    def _parse_expiry(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
