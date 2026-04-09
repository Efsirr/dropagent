"""
Walmart Open API integration.

Fetches product data from Walmart for price comparison.
Requires: WALMART_API_KEY in .env

API Docs: https://developer.walmart.com/
Rate limit: 20 requests/second (Affiliates tier)
"""

import os
from typing import Optional

import httpx

from agent.sources.base import (
    BaseSource,
    ProductCondition,
    SourceProduct,
    StockStatus,
)


# Walmart Affiliate API endpoints
WALMART_SEARCH_URL = "https://developer.api.walmart.com/api-proxy/service/affil/product/v2/search"
WALMART_PRODUCT_URL = "https://developer.api.walmart.com/api-proxy/service/affil/product/v2/items"


class WalmartSource(BaseSource):
    """Walmart Affiliate API client."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: float = 10.0,
    ):
        self._api_key = api_key or os.getenv("WALMART_API_KEY", "")
        self._timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def name(self) -> str:
        return "walmart"

    def _validate_credentials(self):
        if not self._api_key:
            raise ValueError("WALMART_API_KEY is required. Set it in .env")

    def _get_headers(self) -> dict:
        return {
            "WM_SEC.ACCESS_TOKEN": self._api_key,
            "WM_CONSUMER.ID": self._api_key,
            "Accept": "application/json",
        }

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self._timeout)
        return self._client

    async def search(
        self,
        query: str,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 25,
    ) -> list[SourceProduct]:
        """
        Search Walmart products.

        Args:
            query: Search keywords.
            category: Walmart category ID.
            min_price: Min price filter.
            max_price: Max price filter.
            limit: Max results (up to 25 per page).

        Returns:
            List of SourceProduct.
        """
        self._validate_credentials()

        params = {
            "query": query,
            "numItems": min(limit, 25),
            "format": "json",
        }

        if category:
            params["categoryId"] = category
        if min_price is not None:
            params["minPrice"] = str(min_price)
        if max_price is not None:
            params["maxPrice"] = str(max_price)

        client = await self._get_client()
        try:
            response = await client.get(
                WALMART_SEARCH_URL,
                params=params,
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return self._parse_search_response(response.json())
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                return []  # Rate limited
            raise

    async def get_product(self, product_id: str) -> Optional[SourceProduct]:
        """
        Fetch a single product by Walmart item ID.

        Args:
            product_id: Walmart item ID (numeric string).

        Returns:
            SourceProduct or None.
        """
        self._validate_credentials()

        url = f"{WALMART_PRODUCT_URL}/{product_id}"
        params = {"format": "json"}

        client = await self._get_client()
        try:
            response = await client.get(
                url,
                params=params,
                headers=self._get_headers(),
            )
            response.raise_for_status()
            data = response.json()

            # Single item response
            product = self._parse_item(data)
            return product
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (404, 429):
                return None
            raise

    async def get_products(self, product_ids: list[str]) -> list[SourceProduct]:
        """
        Fetch multiple products by ID (Walmart supports batch lookups).

        Args:
            product_ids: List of Walmart item IDs.

        Returns:
            List of SourceProduct.
        """
        self._validate_credentials()

        if not product_ids:
            return []

        # Walmart supports comma-separated IDs (up to 20)
        batch_size = 20
        all_products = []

        for i in range(0, len(product_ids), batch_size):
            batch = product_ids[i : i + batch_size]
            ids_str = ",".join(batch)
            url = f"{WALMART_PRODUCT_URL}"
            params = {"ids": ids_str, "format": "json"}

            client = await self._get_client()
            try:
                response = await client.get(
                    url,
                    params=params,
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                data = response.json()

                items = data.get("items", [])
                for item_data in items:
                    product = self._parse_item(item_data)
                    if product:
                        all_products.append(product)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    break  # Stop on rate limit
                raise

        return all_products

    def _parse_search_response(self, data: dict) -> list[SourceProduct]:
        """Parse Walmart search response."""
        items = data.get("items", [])
        products = []
        for item_data in items:
            product = self._parse_item(item_data)
            if product:
                products.append(product)
        return products

    def _parse_item(self, item: dict) -> Optional[SourceProduct]:
        """Parse a single Walmart item into SourceProduct."""
        try:
            item_id = str(item.get("itemId", ""))
            if not item_id:
                return None

            # Price
            sale_price = item.get("salePrice", item.get("msrp", 0))
            if not sale_price or sale_price <= 0:
                return None

            # Stock status
            stock_str = item.get("stock", "").lower()
            if stock_str == "available":
                stock = StockStatus.IN_STOCK
            elif stock_str == "limited supply":
                stock = StockStatus.LOW_STOCK
            elif stock_str in ("not available", "out of stock"):
                stock = StockStatus.OUT_OF_STOCK
            else:
                stock = StockStatus.UNKNOWN

            # Shipping
            free_shipping = item.get("freeShippingOver35", False)
            shipping_cost = 0.0 if (free_shipping and sale_price >= 35) else 5.99

            # Product URL
            url = item.get(
                "productUrl",
                f"https://www.walmart.com/ip/{item_id}",
            )
            if url.startswith("//"):
                url = f"https:{url}"

            return SourceProduct(
                source="walmart",
                source_id=item_id,
                url=url,
                title=item.get("name", "Unknown Product"),
                price=float(sale_price),
                currency="USD",
                condition=ProductCondition.NEW,
                category=item.get("categoryPath", None),
                brand=item.get("brandName", None),
                image_url=item.get("largeImage", item.get("mediumImage")),
                upc=item.get("upc"),
                stock_status=stock,
                seller=item.get("sellerInfo", "Walmart"),
                ships_from="US",
                shipping_cost=shipping_cost,
                rating=item.get("customerRating"),
                review_count=item.get("numReviews"),
            )
        except (KeyError, ValueError, TypeError):
            return None

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
