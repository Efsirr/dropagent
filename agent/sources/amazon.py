"""
Amazon Product Advertising API (PA-API 5.0) integration.

Fetches product data from Amazon for price comparison.
Requires: AMAZON_ACCESS_KEY, AMAZON_SECRET_KEY, AMAZON_PARTNER_TAG in .env

API Docs: https://webservices.amazon.com/paapi5/documentation/
Rate limit: 1 request/second (scales with revenue)
"""

import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from typing import Optional

import httpx

from agent.sources.base import (
    BaseSource,
    ProductCondition,
    SourceProduct,
    StockStatus,
)


# PA-API 5.0 endpoints by region
AMAZON_ENDPOINTS = {
    "us": "webservices.amazon.com",
    "uk": "webservices.amazon.co.uk",
    "de": "webservices.amazon.de",
    "ca": "webservices.amazon.ca",
}

AMAZON_REGIONS = {
    "us": "us-east-1",
    "uk": "eu-west-1",
    "de": "eu-west-1",
    "ca": "us-east-1",
}


class AmazonSource(BaseSource):
    """Amazon Product Advertising API v5.0 client."""

    def __init__(
        self,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        partner_tag: Optional[str] = None,
        marketplace: str = "us",
        timeout: float = 10.0,
    ):
        self._access_key = access_key or os.getenv("AMAZON_ACCESS_KEY", "")
        self._secret_key = secret_key or os.getenv("AMAZON_SECRET_KEY", "")
        self._partner_tag = partner_tag or os.getenv("AMAZON_PARTNER_TAG", "")
        self._marketplace = marketplace
        self._host = AMAZON_ENDPOINTS.get(marketplace, AMAZON_ENDPOINTS["us"])
        self._region = AMAZON_REGIONS.get(marketplace, AMAZON_REGIONS["us"])
        self._timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def name(self) -> str:
        return "amazon"

    def _validate_credentials(self):
        """Check all required credentials are set."""
        if not self._access_key:
            raise ValueError("AMAZON_ACCESS_KEY is required")
        if not self._secret_key:
            raise ValueError("AMAZON_SECRET_KEY is required")
        if not self._partner_tag:
            raise ValueError("AMAZON_PARTNER_TAG is required")

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self._timeout)
        return self._client

    def _sign_request(self, payload: str, timestamp: datetime) -> dict:
        """
        Generate AWS Signature v4 headers for PA-API request.

        Returns headers dict ready to send.
        """
        service = "ProductAdvertisingAPI"
        date_stamp = timestamp.strftime("%Y%m%d")
        amz_date = timestamp.strftime("%Y%m%dT%H%M%SZ")
        path = "/paapi5/searchitems"
        content_type = "application/json; charset=UTF-8"

        # Step 1: Create canonical request
        canonical_headers = (
            f"content-encoding:amz-1.0\n"
            f"content-type:{content_type}\n"
            f"host:{self._host}\n"
            f"x-amz-date:{amz_date}\n"
            f"x-amz-target:com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems\n"
        )
        signed_headers = "content-encoding;content-type;host;x-amz-date;x-amz-target"

        payload_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        canonical_request = (
            f"POST\n{path}\n\n{canonical_headers}\n{signed_headers}\n{payload_hash}"
        )

        # Step 2: Create string to sign
        credential_scope = f"{date_stamp}/{self._region}/{service}/aws4_request"
        string_to_sign = (
            f"AWS4-HMAC-SHA256\n{amz_date}\n{credential_scope}\n"
            + hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
        )

        # Step 3: Calculate signature
        def _hmac_sign(key: bytes, msg: str) -> bytes:
            return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

        signing_key = _hmac_sign(
            _hmac_sign(
                _hmac_sign(
                    _hmac_sign(
                        f"AWS4{self._secret_key}".encode("utf-8"),
                        date_stamp,
                    ),
                    self._region,
                ),
                service,
            ),
            "aws4_request",
        )

        signature = hmac.new(
            signing_key, string_to_sign.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        # Step 4: Build authorization header
        authorization = (
            f"AWS4-HMAC-SHA256 "
            f"Credential={self._access_key}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, "
            f"Signature={signature}"
        )

        return {
            "Authorization": authorization,
            "Content-Encoding": "amz-1.0",
            "Content-Type": content_type,
            "Host": self._host,
            "X-Amz-Date": amz_date,
            "X-Amz-Target": "com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems",
        }

    async def search(
        self,
        query: str,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 10,
    ) -> list[SourceProduct]:
        """
        Search Amazon products via PA-API 5.0 SearchItems.

        Args:
            query: Search keywords.
            category: Amazon search index (e.g. "Electronics", "Toys").
            min_price: Min price in USD (converted to cents for API).
            max_price: Max price in USD (converted to cents for API).
            limit: Max results (1-10 per API call).

        Returns:
            List of SourceProduct.
        """
        self._validate_credentials()

        payload = {
            "Keywords": query,
            "SearchIndex": category or "All",
            "ItemCount": min(limit, 10),  # PA-API max is 10 per request
            "PartnerTag": self._partner_tag,
            "PartnerType": "Associates",
            "Marketplace": f"www.amazon.com",
            "Resources": [
                "Images.Primary.Large",
                "ItemInfo.Title",
                "ItemInfo.ByLineInfo",
                "ItemInfo.Classifications",
                "ItemInfo.ExternalIds",
                "Offers.Listings.Price",
                "Offers.Listings.DeliveryInfo.IsFreeShippingEligible",
                "Offers.Listings.Availability.Type",
                "Offers.Listings.Condition",
                "Offers.Listings.MerchantInfo",
                "BrowseNodeInfo.BrowseNodes.SalesRank",
            ],
        }

        # Price filters (PA-API uses cents)
        if min_price is not None:
            payload["MinPrice"] = int(min_price * 100)
        if max_price is not None:
            payload["MaxPrice"] = int(max_price * 100)

        payload_str = json.dumps(payload)
        timestamp = datetime.now(timezone.utc)
        headers = self._sign_request(payload_str, timestamp)

        client = await self._get_client()
        try:
            response = await client.post(
                f"https://{self._host}/paapi5/searchitems",
                content=payload_str,
                headers=headers,
            )
            response.raise_for_status()
            return self._parse_search_response(response.json())
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                return []  # Rate limited — return empty
            raise

    async def get_product(self, product_id: str) -> Optional[SourceProduct]:
        """
        Fetch a single product by ASIN via PA-API 5.0 GetItems.

        Args:
            product_id: Amazon ASIN (e.g. "B09V3KXJPB").

        Returns:
            SourceProduct or None.
        """
        self._validate_credentials()

        payload = {
            "ItemIds": [product_id],
            "PartnerTag": self._partner_tag,
            "PartnerType": "Associates",
            "Marketplace": "www.amazon.com",
            "Resources": [
                "Images.Primary.Large",
                "ItemInfo.Title",
                "ItemInfo.ByLineInfo",
                "ItemInfo.Classifications",
                "ItemInfo.ExternalIds",
                "Offers.Listings.Price",
                "Offers.Listings.DeliveryInfo.IsFreeShippingEligible",
                "Offers.Listings.Availability.Type",
                "Offers.Listings.Condition",
                "Offers.Listings.MerchantInfo",
            ],
        }

        payload_str = json.dumps(payload)
        timestamp = datetime.now(timezone.utc)

        # Adjust signing for GetItems endpoint
        headers = self._sign_request(payload_str, timestamp)
        headers["X-Amz-Target"] = (
            "com.amazon.paapi5.v1.ProductAdvertisingAPIv1.GetItems"
        )

        client = await self._get_client()
        try:
            response = await client.post(
                f"https://{self._host}/paapi5/getitems",
                content=payload_str,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            items = self._parse_items(data.get("ItemsResult", {}).get("Items", []))
            return items[0] if items else None
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                return None
            raise

    def _parse_search_response(self, data: dict) -> list[SourceProduct]:
        """Parse SearchItems API response."""
        items = data.get("SearchResult", {}).get("Items", [])
        return self._parse_items(items)

    def _parse_items(self, items: list[dict]) -> list[SourceProduct]:
        """Parse a list of PA-API item objects into SourceProduct list."""
        products = []

        for item in items:
            try:
                asin = item.get("ASIN", "")
                detail_url = item.get("DetailPageURL", f"https://www.amazon.com/dp/{asin}")

                # Title
                title = (
                    item.get("ItemInfo", {})
                    .get("Title", {})
                    .get("DisplayValue", "Unknown Product")
                )

                # Brand
                brand = (
                    item.get("ItemInfo", {})
                    .get("ByLineInfo", {})
                    .get("Brand", {})
                    .get("DisplayValue")
                )

                # Category
                category = (
                    item.get("ItemInfo", {})
                    .get("Classifications", {})
                    .get("Binding", {})
                    .get("DisplayValue")
                )

                # UPC
                upc = None
                ext_ids = item.get("ItemInfo", {}).get("ExternalIds", {})
                upcs = ext_ids.get("UPCs", {}).get("DisplayValues", [])
                if upcs:
                    upc = upcs[0]

                # Image
                image_url = (
                    item.get("Images", {})
                    .get("Primary", {})
                    .get("Large", {})
                    .get("URL")
                )

                # Price & offer info
                offers = item.get("Offers", {}).get("Listings", [])
                if not offers:
                    continue  # Skip products with no price

                offer = offers[0]
                price = float(
                    offer.get("Price", {}).get("Amount", 0)
                )
                currency = offer.get("Price", {}).get("Currency", "USD")

                # Condition
                cond_str = (
                    offer.get("Condition", {})
                    .get("Value", "New")
                    .lower()
                )
                condition = {
                    "new": ProductCondition.NEW,
                    "used": ProductCondition.USED,
                    "refurbished": ProductCondition.REFURBISHED,
                }.get(cond_str, ProductCondition.UNKNOWN)

                # Stock
                avail_type = (
                    offer.get("Availability", {})
                    .get("Type", "")
                )
                stock = StockStatus.IN_STOCK if avail_type == "Now" else StockStatus.UNKNOWN

                # Shipping
                free_shipping = (
                    offer.get("DeliveryInfo", {})
                    .get("IsFreeShippingEligible", False)
                )
                shipping_cost = 0.0 if free_shipping else 5.99

                # Seller
                seller = (
                    offer.get("MerchantInfo", {})
                    .get("Name", "Amazon")
                )

                products.append(
                    SourceProduct(
                        source="amazon",
                        source_id=asin,
                        url=detail_url,
                        title=title,
                        price=price,
                        currency=currency,
                        condition=condition,
                        category=category,
                        brand=brand,
                        image_url=image_url,
                        upc=upc,
                        stock_status=stock,
                        seller=seller,
                        ships_from="US",
                        shipping_cost=shipping_cost,
                    )
                )
            except (KeyError, ValueError, TypeError):
                continue  # Skip malformed items

        return products

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
