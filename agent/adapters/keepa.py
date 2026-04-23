"""Keepa adapter — Amazon price history enrichment.

Uses the user's saved Keepa API key to fetch Amazon price history
for ASINs. Converts Keepa's compact delta-compressed format into
clean time-series data usable by the analyzer and watchlist.

Keepa time is minutes since 2011-01-01 00:00 UTC.
Prices are in cents (divide by 100 for dollars).
A value of -1 means out-of-stock / no data at that timestamp.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)

# Keepa epoch: 2011-01-01 00:00 UTC
_KEEPA_EPOCH = datetime(2011, 1, 1, tzinfo=timezone.utc)
_KEEPA_BASE_URL = "https://api.keepa.com"

# CSV array indices for price types
CSV_AMAZON = 0          # Amazon direct price
CSV_NEW = 1             # Lowest new (marketplace)
CSV_USED = 2            # Lowest used
CSV_SALES_RANK = 3      # Sales rank
CSV_BUY_BOX = 18        # Buy box price
CSV_NEW_FBM = 7         # New (FBM / merchant fulfilled)


@dataclass
class PricePoint:
    """A single historical price observation."""

    timestamp: datetime
    price_usd: Optional[float]   # None = out of stock at this time
    price_type: str              # "amazon", "new", "used", "buy_box"

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "price_usd": self.price_usd,
            "price_type": self.price_type,
        }


@dataclass
class KeepaProduct:
    """Parsed Keepa product data with price history."""

    asin: str
    title: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    sales_rank: Optional[int] = None
    current_amazon_price: Optional[float] = None
    current_new_price: Optional[float] = None
    current_buy_box_price: Optional[float] = None

    # Historical data
    amazon_history: list[PricePoint] = field(default_factory=list)
    new_history: list[PricePoint] = field(default_factory=list)
    buy_box_history: list[PricePoint] = field(default_factory=list)

    # Stats
    price_30d_avg: Optional[float] = None
    price_90d_avg: Optional[float] = None
    price_30d_min: Optional[float] = None
    price_30d_max: Optional[float] = None
    price_drops_90d: int = 0

    def to_dict(self) -> dict:
        return {
            "asin": self.asin,
            "title": self.title,
            "brand": self.brand,
            "category": self.category,
            "sales_rank": self.sales_rank,
            "current_amazon_price": self.current_amazon_price,
            "current_new_price": self.current_new_price,
            "current_buy_box_price": self.current_buy_box_price,
            "amazon_history": [p.to_dict() for p in self.amazon_history],
            "new_history": [p.to_dict() for p in self.new_history],
            "buy_box_history": [p.to_dict() for p in self.buy_box_history],
            "price_30d_avg": self.price_30d_avg,
            "price_90d_avg": self.price_90d_avg,
            "price_30d_min": self.price_30d_min,
            "price_30d_max": self.price_30d_max,
            "price_drops_90d": self.price_drops_90d,
        }


def keepa_time_to_datetime(keepa_minutes: int) -> datetime:
    """Convert Keepa minutes to UTC datetime."""
    return _KEEPA_EPOCH + timedelta(minutes=keepa_minutes)


def datetime_to_keepa_time(dt: datetime) -> int:
    """Convert UTC datetime to Keepa minutes."""
    delta = dt - _KEEPA_EPOCH
    return int(delta.total_seconds() / 60)


def _parse_csv_pairs(
    csv_array: list[int],
    price_type: str,
    is_price: bool = True,
) -> list[PricePoint]:
    """Parse Keepa's flat [time, value, time, value, ...] array into PricePoints.

    Args:
        csv_array: Flat array of alternating [keepa_time, value, ...].
        price_type: Label like "amazon", "new", "buy_box".
        is_price: If True, divide value by 100 and treat -1 as None.
    """
    if not csv_array:
        return []

    points = []
    for i in range(0, len(csv_array) - 1, 2):
        keepa_time = csv_array[i]
        raw_value = csv_array[i + 1]

        timestamp = keepa_time_to_datetime(keepa_time)

        if is_price:
            price = None if raw_value < 0 else round(raw_value / 100, 2)
        else:
            price = None if raw_value < 0 else float(raw_value)

        points.append(PricePoint(
            timestamp=timestamp,
            price_usd=price,
            price_type=price_type,
        ))

    return points


def _compute_stats(
    history: list[PricePoint],
    now: Optional[datetime] = None,
) -> dict:
    """Compute price statistics over the last 30 and 90 days."""
    now = now or datetime.now(timezone.utc)
    cutoff_30 = now - timedelta(days=30)
    cutoff_90 = now - timedelta(days=90)

    prices_30 = [p.price_usd for p in history
                 if p.price_usd is not None and p.timestamp >= cutoff_30]
    prices_90 = [p.price_usd for p in history
                 if p.price_usd is not None and p.timestamp >= cutoff_90]

    # Count price drops in 90 days (a drop = current < previous by >5%)
    drops_90 = 0
    recent = [p for p in history if p.timestamp >= cutoff_90 and p.price_usd is not None]
    for i in range(1, len(recent)):
        prev = recent[i - 1].price_usd
        curr = recent[i].price_usd
        if prev and curr and curr < prev * 0.95:
            drops_90 += 1

    return {
        "price_30d_avg": round(sum(prices_30) / len(prices_30), 2) if prices_30 else None,
        "price_90d_avg": round(sum(prices_90) / len(prices_90), 2) if prices_90 else None,
        "price_30d_min": round(min(prices_30), 2) if prices_30 else None,
        "price_30d_max": round(max(prices_30), 2) if prices_30 else None,
        "price_drops_90d": drops_90,
    }


class KeepaAdapter:
    """Fetch and parse Amazon price history from the Keepa API.

    Usage with user's saved key:
        adapter = KeepaAdapter(api_key=decrypted_key)
        product = await adapter.get_product("B09V3KXJPB")
    """

    def __init__(self, api_key: str, domain_id: int = 1):
        """Init Keepa adapter.

        Args:
            api_key: Keepa API key (decrypted from user's saved credentials).
            domain_id: Amazon domain. 1=.com, 3=.co.uk, 4=.de, 5=.fr, etc.
        """
        if not api_key or not api_key.strip():
            raise ValueError("Keepa API key is required")
        self._api_key = api_key.strip()
        self._domain_id = domain_id
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
            )
        return self._session

    async def get_product(self, asin: str) -> Optional[KeepaProduct]:
        """Fetch full product data including price history for a single ASIN."""
        return (await self.get_products([asin]) or [None])[0]

    async def get_products(self, asins: list[str]) -> list[Optional[KeepaProduct]]:
        """Fetch product data for multiple ASINs (max 100 per request).

        Args:
            asins: List of Amazon ASINs.

        Returns:
            List of KeepaProduct (or None for unfound ASINs), same order.
        """
        if not asins:
            return []

        # Keepa allows up to 100 ASINs per request
        batch = asins[:100]
        params = {
            "key": self._api_key,
            "domain": str(self._domain_id),
            "asin": ",".join(batch),
            "history": "1",   # include price history
            "stats": "90",    # include 90-day stats
        }

        session = await self._get_session()
        try:
            async with session.get(
                f"{_KEEPA_BASE_URL}/product",
                params=params,
            ) as resp:
                if resp.status == 429:
                    logger.warning("Keepa rate limit reached, retry later")
                    return [None] * len(batch)
                if resp.status == 401:
                    logger.error("Keepa API key invalid or expired")
                    return [None] * len(batch)
                if resp.status != 200:
                    body = await resp.text()
                    logger.error("Keepa API error %d: %s", resp.status, body[:200])
                    return [None] * len(batch)

                data = await resp.json()
        except (aiohttp.ClientError, TimeoutError) as exc:
            logger.error("Keepa request failed: %s", exc)
            return [None] * len(batch)

        products_data = data.get("products") or []
        result_map: dict[str, KeepaProduct] = {}

        for item in products_data:
            parsed = self._parse_product(item)
            if parsed:
                result_map[parsed.asin] = parsed

        # Return in the same order as input ASINs
        return [result_map.get(asin) for asin in batch]

    async def get_token_status(self) -> dict:
        """Check remaining API tokens."""
        session = await self._get_session()
        try:
            async with session.get(
                f"{_KEEPA_BASE_URL}/token",
                params={"key": self._api_key},
            ) as resp:
                if resp.status != 200:
                    return {"error": f"HTTP {resp.status}"}
                data = await resp.json()
                return {
                    "tokens_left": data.get("tokensLeft", 0),
                    "refill_in": data.get("refillIn", 0),
                    "refill_rate": data.get("refillRate", 0),
                }
        except (aiohttp.ClientError, TimeoutError) as exc:
            return {"error": str(exc)}

    def _parse_product(self, item: dict) -> Optional[KeepaProduct]:
        """Parse a single Keepa API product object into KeepaProduct."""
        asin = item.get("asin")
        if not asin:
            return None

        csv = item.get("csv") or []

        # Parse price histories from CSV arrays
        amazon_history = _parse_csv_pairs(
            csv[CSV_AMAZON] if len(csv) > CSV_AMAZON and csv[CSV_AMAZON] else [],
            "amazon",
        )
        new_history = _parse_csv_pairs(
            csv[CSV_NEW] if len(csv) > CSV_NEW and csv[CSV_NEW] else [],
            "new",
        )
        buy_box_history = _parse_csv_pairs(
            csv[CSV_BUY_BOX] if len(csv) > CSV_BUY_BOX and csv[CSV_BUY_BOX] else [],
            "buy_box",
        )

        # Extract current prices from stats
        stats = item.get("stats") or {}
        current = stats.get("current") or []

        current_amazon = None
        if len(current) > CSV_AMAZON and current[CSV_AMAZON] and current[CSV_AMAZON] > 0:
            current_amazon = round(current[CSV_AMAZON] / 100, 2)

        current_new = None
        if len(current) > CSV_NEW and current[CSV_NEW] and current[CSV_NEW] > 0:
            current_new = round(current[CSV_NEW] / 100, 2)

        current_buy_box = None
        if len(current) > CSV_BUY_BOX and current[CSV_BUY_BOX] and current[CSV_BUY_BOX] > 0:
            current_buy_box = round(current[CSV_BUY_BOX] / 100, 2)

        # Compute stats from Amazon history
        price_stats = _compute_stats(amazon_history)

        product = KeepaProduct(
            asin=asin,
            title=item.get("title"),
            brand=item.get("brand"),
            category=item.get("categoryTree", [{}])[0].get("name") if item.get("categoryTree") else None,
            sales_rank=item.get("salesRankCurrent"),
            current_amazon_price=current_amazon,
            current_new_price=current_new,
            current_buy_box_price=current_buy_box,
            amazon_history=amazon_history,
            new_history=new_history,
            buy_box_history=buy_box_history,
            price_30d_avg=price_stats["price_30d_avg"],
            price_90d_avg=price_stats["price_90d_avg"],
            price_30d_min=price_stats["price_30d_min"],
            price_30d_max=price_stats["price_30d_max"],
            price_drops_90d=price_stats["price_drops_90d"],
        )
        return product

    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()


def get_keepa_adapter_for_user(
    telegram_chat_id: str,
    session,
    app_secret: Optional[str] = None,
) -> Optional[KeepaAdapter]:
    """Create a KeepaAdapter using the user's saved encrypted key.

    Args:
        telegram_chat_id: User's Telegram chat ID.
        session: SQLAlchemy database session.
        app_secret: App-level encryption secret (from env).

    Returns:
        KeepaAdapter or None if no key is saved.
    """
    from db.service import get_user_integration_encrypted_secret
    from agent.integrations import deserialize_integration_credentials
    from agent.secrets import open_secret

    app_secret = app_secret or os.environ.get("APP_SECRET_KEY", "")
    if not app_secret or len(app_secret) < 16:
        logger.warning("APP_SECRET_KEY not configured, cannot decrypt user keys")
        return None

    encrypted = get_user_integration_encrypted_secret(
        session=session,
        telegram_chat_id=telegram_chat_id,
        integration_id="keepa",
    )
    if not encrypted:
        return None

    try:
        api_key = deserialize_integration_credentials(
            "keepa",
            open_secret(encrypted, app_secret),
        ).get("api_key", "")
    except Exception as exc:
        logger.error("Failed to decrypt Keepa key for user %s: %s", telegram_chat_id, exc)
        return None

    if not api_key:
        return None
    return KeepaAdapter(api_key=api_key)
