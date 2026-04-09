"""
eBay Sold Listings Scanner for DropAgent.

Searches eBay's completed/sold listings to find:
- What products are actually selling
- Average sold prices
- Sales velocity (how many sold recently)

Uses the eBay Browse API (Finding API fallback).
Results feed into the analyzer for margin calculations.
"""

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import httpx

from i18n import t


# eBay API endpoints
EBAY_BROWSE_API = "https://api.ebay.com/buy/browse/v1/item_summary/search"
EBAY_FINDING_API = "https://svcs.ebay.com/services/search/FindingService/v1"


@dataclass
class SoldItem:
    """A single sold listing from eBay."""
    title: str
    sold_price: float
    currency: str
    sold_date: Optional[datetime]
    condition: str
    item_id: str
    image_url: Optional[str] = None
    seller: Optional[str] = None
    category: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "sold_price": self.sold_price,
            "currency": self.currency,
            "sold_date": self.sold_date.isoformat() if self.sold_date else None,
            "condition": self.condition,
            "item_id": self.item_id,
            "image_url": self.image_url,
            "seller": self.seller,
            "category": self.category,
        }


@dataclass
class ScanResult:
    """Aggregated results from a sold listings search."""
    query: str
    items: list[SoldItem]
    total_found: int

    @property
    def avg_price(self) -> float:
        if not self.items:
            return 0.0
        return round(sum(i.sold_price for i in self.items) / len(self.items), 2)

    @property
    def min_price(self) -> float:
        if not self.items:
            return 0.0
        return min(i.sold_price for i in self.items)

    @property
    def max_price(self) -> float:
        if not self.items:
            return 0.0
        return max(i.sold_price for i in self.items)

    @property
    def count(self) -> int:
        return len(self.items)

    def summary(self, lang: Optional[str] = None) -> str:
        """Human-readable summary of scan results."""
        sep = "=" * 50
        thin = "─" * 50

        if not self.items:
            return f"{sep}\n  {t('scanner.no_results', lang=lang)}\n{sep}"

        lines = [
            sep,
            f"  {t('scanner.title', lang=lang)}",
            f"  {t('scanner.found', lang=lang, count=self.count, query=self.query)}",
            sep,
            f"  {t('scanner.avg_price', lang=lang) + ':':<22}${self.avg_price:.2f}",
            f"  {t('scanner.price_range', lang=lang) + ':':<22}${self.min_price:.2f} — ${self.max_price:.2f}",
            f"  {t('scanner.total_sold', lang=lang) + ':':<22}{self.total_found}",
            thin,
        ]

        # Top 5 items
        for i, item in enumerate(self.items[:5], 1):
            lines.append(f"  {i}. ${item.sold_price:.2f} — {item.title[:60]}")

        if self.count > 5:
            lines.append(f"  ... and {self.count - 5} more")

        lines.append(sep)
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "total_found": self.total_found,
            "count": self.count,
            "avg_price": self.avg_price,
            "min_price": self.min_price,
            "max_price": self.max_price,
            "items": [item.to_dict() for item in self.items],
        }


class EbayScanner:
    """Scans eBay sold/completed listings."""

    def __init__(self, app_id: Optional[str] = None, timeout: float = 15.0):
        self.app_id = app_id or os.getenv("EBAY_APP_ID", "")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def search_sold(
        self,
        query: str,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        category_id: Optional[str] = None,
        condition: Optional[str] = None,
        seller: Optional[str] = None,
        limit: int = 50,
    ) -> ScanResult:
        """
        Search eBay completed/sold listings.

        Args:
            query: Search keywords (e.g. "airpods pro").
            min_price: Minimum sold price filter.
            max_price: Maximum sold price filter.
            category_id: eBay category ID to narrow results.
            condition: "New", "Used", or None for all.
            limit: Max items to return (up to 200).

        Returns:
            ScanResult with sold items and aggregated stats.
        """
        if not self.app_id:
            raise ValueError(
                "EBAY_APP_ID is required. Set it in .env or pass to EbayScanner(app_id=...)"
            )

        params = self._build_finding_params(
            query, min_price, max_price, category_id, condition, seller, limit
        )

        client = await self._get_client()
        try:
            response = await client.get(EBAY_FINDING_API, params=params)
            response.raise_for_status()
            return self._parse_finding_response(query, response.json())
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                # Rate limited — return empty result instead of crashing
                return ScanResult(query=query, items=[], total_found=0)
            raise

    def _build_finding_params(
        self,
        query: str,
        min_price: Optional[float],
        max_price: Optional[float],
        category_id: Optional[str],
        condition: Optional[str],
        seller: Optional[str],
        limit: int,
    ) -> dict:
        """Build request parameters for the Finding API."""
        params = {
            "OPERATION-NAME": "findCompletedItems",
            "SERVICE-VERSION": "1.13.0",
            "SECURITY-APPNAME": self.app_id,
            "RESPONSE-DATA-FORMAT": "JSON",
            "REST-PAYLOAD": "true",
            "keywords": query,
            "paginationInput.entriesPerPage": str(min(limit, 100)),
            # Only sold items (not just completed/unsold)
            "itemFilter(0).name": "SoldItemsOnly",
            "itemFilter(0).value": "true",
            "sortOrder": "EndTimeSoonest",
        }

        filter_idx = 1

        if min_price is not None:
            params[f"itemFilter({filter_idx}).name"] = "MinPrice"
            params[f"itemFilter({filter_idx}).value"] = str(min_price)
            params[f"itemFilter({filter_idx}).paramName"] = "Currency"
            params[f"itemFilter({filter_idx}).paramValue"] = "USD"
            filter_idx += 1

        if max_price is not None:
            params[f"itemFilter({filter_idx}).name"] = "MaxPrice"
            params[f"itemFilter({filter_idx}).value"] = str(max_price)
            params[f"itemFilter({filter_idx}).paramName"] = "Currency"
            params[f"itemFilter({filter_idx}).paramValue"] = "USD"
            filter_idx += 1

        if category_id:
            params["categoryId"] = category_id

        if condition:
            condition_map = {"new": "1000", "used": "3000", "refurbished": "2500"}
            cid = condition_map.get(condition.lower(), condition)
            params[f"itemFilter({filter_idx}).name"] = "Condition"
            params[f"itemFilter({filter_idx}).value"] = cid
            filter_idx += 1

        if seller:
            params[f"itemFilter({filter_idx}).name"] = "Seller"
            params[f"itemFilter({filter_idx}).value"] = seller

        return params

    def _parse_finding_response(self, query: str, data: dict) -> ScanResult:
        """Parse the Finding API JSON response into ScanResult."""
        items = []

        try:
            search_result = (
                data.get("findCompletedItemsResponse", [{}])[0]
                .get("searchResult", [{}])[0]
            )
            total_found = int(search_result.get("@count", "0"))
            raw_items = search_result.get("item", [])
        except (IndexError, KeyError):
            return ScanResult(query=query, items=[], total_found=0)

        for raw in raw_items:
            try:
                # Extract price
                selling = raw.get("sellingStatus", [{}])[0]
                price_data = selling.get("currentPrice", [{}])[0]
                price = float(price_data.get("__value__", "0"))
                currency = price_data.get("@currencyId", "USD")

                # Extract date
                end_time = raw.get("listingInfo", [{}])[0].get("endTime", [None])[0]
                sold_date = None
                if end_time:
                    sold_date = datetime.fromisoformat(
                        end_time.replace("Z", "+00:00")
                    )

                # Extract condition
                cond = raw.get("condition", [{}])[0].get("conditionDisplayName", ["N/A"])[0]

                item = SoldItem(
                    title=raw.get("title", [""])[0],
                    sold_price=price,
                    currency=currency,
                    sold_date=sold_date,
                    condition=cond,
                    item_id=raw.get("itemId", [""])[0],
                    image_url=raw.get("galleryURL", [None])[0],
                    seller=raw.get("sellerInfo", [{}])[0].get("sellerUserName", [None])[0],
                    category=raw.get("primaryCategory", [{}])[0].get("categoryName", [None])[0],
                )
                items.append(item)
            except (IndexError, KeyError, ValueError):
                continue  # Skip malformed items

        return ScanResult(query=query, items=items, total_found=total_found)

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
