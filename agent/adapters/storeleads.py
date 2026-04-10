"""StoreLeads adapter — competitor store discovery and intelligence.

Uses the user's saved StoreLeads API key to look up competitor stores
by domain name or discover stores matching specific criteria.

StoreLeads API docs: https://storeleads.app/api
Authentication: Bearer token in Authorization header.
Rate limits: varies by plan, HTTP 429 with Retry-After header.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)

_STORELEADS_BASE_URL = "https://storeleads.app/json/api/v1/all"


@dataclass
class StoreContact:
    """A contact method for a store (email, phone, social)."""

    contact_type: str      # "email", "phone", "twitter", "instagram", etc.
    value: str             # email address, URL, phone number
    followers: Optional[int] = None
    followers_30d: Optional[int] = None

    def to_dict(self) -> dict:
        d = {"type": self.contact_type, "value": self.value}
        if self.followers is not None:
            d["followers"] = self.followers
        if self.followers_30d is not None:
            d["followers_30d"] = self.followers_30d
        return d


@dataclass
class StoreApp:
    """An app installed on a competitor store."""

    name: str
    token: str
    platform: str
    installs: int = 0
    rating: Optional[str] = None
    categories: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "token": self.token,
            "platform": self.platform,
            "installs": self.installs,
            "rating": self.rating,
            "categories": self.categories,
        }


@dataclass
class StoreDomain:
    """Parsed store data from StoreLeads."""

    domain: str
    merchant_name: Optional[str] = None
    platform: Optional[str] = None          # "shopify", "woocommerce", etc.
    plan: Optional[str] = None              # "Shopify Plus", etc.
    state: Optional[str] = None             # "Active", "Inactive", etc.
    country_code: Optional[str] = None
    currency_code: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None

    # Product metrics
    product_count: Optional[int] = None
    avg_price_usd: Optional[float] = None   # in dollars
    min_price_usd: Optional[float] = None
    max_price_usd: Optional[float] = None
    vendor_count: Optional[int] = None

    # Traffic estimates
    estimated_visits: Optional[int] = None
    estimated_sales_monthly_usd: Optional[float] = None
    rank: Optional[int] = None
    platform_rank: Optional[int] = None

    # Social / contact
    contacts: list[StoreContact] = field(default_factory=list)
    apps: list[StoreApp] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    features: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "domain": self.domain,
            "merchant_name": self.merchant_name,
            "platform": self.platform,
            "plan": self.plan,
            "state": self.state,
            "country_code": self.country_code,
            "currency_code": self.currency_code,
            "location": self.location,
            "description": self.description,
            "product_count": self.product_count,
            "avg_price_usd": self.avg_price_usd,
            "min_price_usd": self.min_price_usd,
            "max_price_usd": self.max_price_usd,
            "vendor_count": self.vendor_count,
            "estimated_visits": self.estimated_visits,
            "estimated_sales_monthly_usd": self.estimated_sales_monthly_usd,
            "rank": self.rank,
            "platform_rank": self.platform_rank,
            "contacts": [c.to_dict() for c in self.contacts],
            "apps": [a.to_dict() for a in self.apps],
            "categories": self.categories,
            "features": self.features,
        }


class StoreLeadsAdapter:
    """Fetch competitor store intelligence from the StoreLeads API.

    Usage with user's saved key:
        adapter = StoreLeadsAdapter(api_key=decrypted_key)
        store = await adapter.get_domain("www.aloyoga.com")
    """

    def __init__(self, api_key: str):
        if not api_key or not api_key.strip():
            raise ValueError("StoreLeads API key is required")
        self._api_key = api_key.strip()
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={"Authorization": f"Bearer {self._api_key}"},
            )
        return self._session

    async def get_domain(self, domain_name: str) -> Optional[StoreDomain]:
        """Look up a single store domain by name."""
        session = await self._get_session()
        try:
            async with session.get(
                f"{_STORELEADS_BASE_URL}/domain/{domain_name}",
                params={"follow_redirects": "true"},
            ) as resp:
                if resp.status == 429:
                    logger.warning("StoreLeads rate limit reached")
                    return None
                if resp.status in (401, 403):
                    logger.error("StoreLeads API key invalid or insufficient access")
                    return None
                if resp.status == 404:
                    return None
                if resp.status != 200:
                    body = await resp.text()
                    logger.error("StoreLeads error %d: %s", resp.status, body[:200])
                    return None
                data = await resp.json()
        except (aiohttp.ClientError, TimeoutError) as exc:
            logger.error("StoreLeads request failed: %s", exc)
            return None

        return self._parse_domain(data.get("domain") or data)

    async def search_domains(
        self,
        *,
        platform: Optional[str] = None,
        country: Optional[str] = None,
        categories: Optional[str] = None,
        min_rank: Optional[int] = None,
        max_rank: Optional[int] = None,
        page: int = 0,
        page_size: int = 20,
    ) -> list[StoreDomain]:
        """Search for stores matching given criteria."""
        params: dict = {"page": str(page), "page_size": str(min(page_size, 50))}
        if platform:
            params["f:p"] = platform
        if country:
            params["f:cc"] = country
        if categories:
            params["f:categories"] = categories
        if min_rank is not None:
            params["f:platform_rank_min"] = str(min_rank)
        if max_rank is not None:
            params["f:platform_rank_max"] = str(max_rank)

        session = await self._get_session()
        try:
            async with session.get(
                f"{_STORELEADS_BASE_URL}/domain",
                params=params,
            ) as resp:
                if resp.status == 429:
                    logger.warning("StoreLeads rate limit reached")
                    return []
                if resp.status in (401, 403):
                    logger.error("StoreLeads API key invalid")
                    return []
                if resp.status != 200:
                    body = await resp.text()
                    logger.error("StoreLeads search error %d: %s", resp.status, body[:200])
                    return []
                data = await resp.json()
        except (aiohttp.ClientError, TimeoutError) as exc:
            logger.error("StoreLeads search failed: %s", exc)
            return []

        domains = data.get("domains") or []
        return [self._parse_domain(d) for d in domains if d]

    def _parse_domain(self, item: dict) -> StoreDomain:
        """Parse a StoreLeads domain response into StoreDomain."""
        contacts = []
        for c in (item.get("contact_info") or []):
            contacts.append(StoreContact(
                contact_type=c.get("type", ""),
                value=c.get("value", ""),
                followers=c.get("followers"),
                followers_30d=c.get("followers_30d"),
            ))

        apps = []
        for a in (item.get("apps") or []):
            apps.append(StoreApp(
                name=a.get("name", ""),
                token=a.get("token", ""),
                platform=a.get("platform", ""),
                installs=a.get("installs", 0),
                rating=a.get("average_rating"),
                categories=a.get("categories") or [],
            ))

        # Prices are in cents of USD
        avg_price = item.get("avg_price_usd")
        min_price = item.get("min_price_usd")
        max_price = item.get("max_price_usd")
        est_sales = item.get("estimated_sales")

        return StoreDomain(
            domain=item.get("name") or item.get("domain", ""),
            merchant_name=item.get("merchant_name"),
            platform=item.get("platform"),
            plan=item.get("plan"),
            state=item.get("state"),
            country_code=item.get("country_code"),
            currency_code=item.get("currency_code"),
            location=item.get("location"),
            description=item.get("description"),
            product_count=item.get("product_count"),
            avg_price_usd=round(avg_price / 100, 2) if avg_price else None,
            min_price_usd=round(min_price / 100, 2) if min_price else None,
            max_price_usd=round(max_price / 100, 2) if max_price else None,
            vendor_count=item.get("vendor_count"),
            estimated_visits=item.get("estimated_visits"),
            estimated_sales_monthly_usd=round(est_sales / 100, 2) if est_sales else None,
            rank=item.get("rank"),
            platform_rank=item.get("platform_rank"),
            contacts=contacts,
            apps=apps,
            categories=item.get("categories") or [],
            features=item.get("features") or [],
        )

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()


def get_storeleads_adapter_for_user(
    telegram_chat_id: str,
    session,
    app_secret: Optional[str] = None,
) -> Optional[StoreLeadsAdapter]:
    """Create a StoreLeadsAdapter using the user's saved encrypted key."""
    from db.service import get_user_integration_encrypted_secret
    from agent.secrets import open_secret

    app_secret = app_secret or os.environ.get("APP_SECRET_KEY", "")
    if not app_secret or len(app_secret) < 16:
        logger.warning("APP_SECRET_KEY not configured, cannot decrypt user keys")
        return None

    encrypted = get_user_integration_encrypted_secret(
        session=session,
        telegram_chat_id=telegram_chat_id,
        integration_id="storeleads",
    )
    if not encrypted:
        return None

    try:
        api_key = open_secret(encrypted, app_secret)
    except Exception as exc:
        logger.error("Failed to decrypt StoreLeads key for user %s: %s", telegram_chat_id, exc)
        return None

    return StoreLeadsAdapter(api_key=api_key)
