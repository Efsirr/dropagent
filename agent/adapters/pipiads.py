"""PiPiADS adapter — TikTok ad spy for viral product discovery.

Uses the user's saved PiPiADS API key to search for winning TikTok ad
creatives and discover trending products. Can optionally fall back to
Minea if configured instead.

This adapter provides a trend signal boost — it's optional, not required
for core functionality.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)

_PIPIADS_BASE_URL = "https://api.pipiads.com/v2"


@dataclass
class TikTokAd:
    """A TikTok advertisement from PiPiADS."""

    ad_id: str
    title: Optional[str] = None
    advertiser: Optional[str] = None
    landing_page: Optional[str] = None
    country: Optional[str] = None

    # Performance metrics
    total_likes: int = 0
    total_comments: int = 0
    total_shares: int = 0
    ad_impressions: Optional[int] = None
    days_running: int = 0

    # Trend signals
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    trend_score: Optional[float] = None    # computed locally

    # Creative
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "ad_id": self.ad_id,
            "title": self.title,
            "advertiser": self.advertiser,
            "landing_page": self.landing_page,
            "country": self.country,
            "total_likes": self.total_likes,
            "total_comments": self.total_comments,
            "total_shares": self.total_shares,
            "ad_impressions": self.ad_impressions,
            "days_running": self.days_running,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "trend_score": self.trend_score,
            "video_url": self.video_url,
            "thumbnail_url": self.thumbnail_url,
        }


@dataclass
class AdSearchResult:
    """Result of an ad search query."""

    ads: list[TikTokAd] = field(default_factory=list)
    total_count: int = 0
    page: int = 0

    def to_dict(self) -> dict:
        return {
            "ads": [a.to_dict() for a in self.ads],
            "total_count": self.total_count,
            "page": self.page,
        }


def compute_trend_score(ad: TikTokAd) -> float:
    """Compute a simple trend score based on engagement and duration.

    Higher score = hotter ad. Formula weights engagement per day.
    """
    engagement = ad.total_likes + ad.total_comments * 3 + ad.total_shares * 5
    days = max(ad.days_running, 1)
    # Engagement per day, with a log bonus for total volume
    import math
    volume_bonus = math.log10(engagement + 1)
    return round(engagement / days * volume_bonus, 2)


class PiPiAdsAdapter:
    """Search TikTok ads via the PiPiADS API.

    Usage:
        adapter = PiPiAdsAdapter(api_key=decrypted_key)
        results = await adapter.search_ads(keyword="dog toy")
    """

    def __init__(self, api_key: str):
        if not api_key or not api_key.strip():
            raise ValueError("PiPiADS API key is required")
        self._api_key = api_key.strip()
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={"Authorization": f"Bearer {self._api_key}"},
            )
        return self._session

    async def search_ads(
        self,
        keyword: str,
        *,
        country: Optional[str] = None,
        sort_by: str = "likes",
        page: int = 0,
        page_size: int = 20,
    ) -> AdSearchResult:
        """Search TikTok ads by keyword.

        Args:
            keyword: Product/niche keyword to search.
            country: 2-letter country filter.
            sort_by: Sort field (likes, comments, shares, days_running).
            page: Page number.
            page_size: Results per page (max 50).
        """
        params: dict = {
            "keyword": keyword,
            "sort": sort_by,
            "page": str(page),
            "page_size": str(min(page_size, 50)),
        }
        if country:
            params["country"] = country.upper()

        session = await self._get_session()
        try:
            async with session.get(
                f"{_PIPIADS_BASE_URL}/ads/search",
                params=params,
            ) as resp:
                if resp.status == 429:
                    logger.warning("PiPiADS rate limit reached")
                    return AdSearchResult()
                if resp.status in (401, 403):
                    logger.error("PiPiADS API key invalid or expired")
                    return AdSearchResult()
                if resp.status != 200:
                    body = await resp.text()
                    logger.error("PiPiADS error %d: %s", resp.status, body[:200])
                    return AdSearchResult()
                data = await resp.json()
        except (aiohttp.ClientError, TimeoutError) as exc:
            logger.error("PiPiADS request failed: %s", exc)
            return AdSearchResult()

        ads_data = data.get("data") or data.get("ads") or []
        ads = [self._parse_ad(a) for a in ads_data if a]

        return AdSearchResult(
            ads=ads,
            total_count=data.get("total") or data.get("total_count") or len(ads),
            page=page,
        )

    async def get_ad(self, ad_id: str) -> Optional[TikTokAd]:
        """Fetch details for a single ad by ID."""
        session = await self._get_session()
        try:
            async with session.get(
                f"{_PIPIADS_BASE_URL}/ads/{ad_id}",
            ) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
        except (aiohttp.ClientError, TimeoutError) as exc:
            logger.error("PiPiADS get_ad failed: %s", exc)
            return None

        ad_data = data.get("data") or data.get("ad") or data
        return self._parse_ad(ad_data) if ad_data.get("id") or ad_data.get("ad_id") else None

    def _parse_ad(self, item: dict) -> TikTokAd:
        """Parse a PiPiADS ad item into TikTokAd."""
        ad = TikTokAd(
            ad_id=str(item.get("id") or item.get("ad_id", "")),
            title=item.get("title") or item.get("ad_title"),
            advertiser=item.get("advertiser") or item.get("advertiser_name"),
            landing_page=item.get("landing_page") or item.get("url"),
            country=item.get("country"),
            total_likes=item.get("likes") or item.get("total_likes") or 0,
            total_comments=item.get("comments") or item.get("total_comments") or 0,
            total_shares=item.get("shares") or item.get("total_shares") or 0,
            ad_impressions=item.get("impressions") or item.get("ad_impressions"),
            days_running=item.get("days_running") or item.get("duration") or 0,
            first_seen=item.get("first_seen") or item.get("created_at"),
            last_seen=item.get("last_seen") or item.get("updated_at"),
            video_url=item.get("video_url"),
            thumbnail_url=item.get("thumbnail_url") or item.get("cover_url"),
        )
        ad.trend_score = compute_trend_score(ad)
        return ad

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()


def get_pipiads_adapter_for_user(
    telegram_chat_id: str,
    session,
    app_secret: Optional[str] = None,
) -> Optional[PiPiAdsAdapter]:
    """Create a PiPiAdsAdapter using the user's saved encrypted key."""
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
        integration_id="pipiads",
    )
    if not encrypted:
        return None

    try:
        api_key = deserialize_integration_credentials(
            "pipiads",
            open_secret(encrypted, app_secret),
        ).get("api_key", "")
    except Exception as exc:
        logger.error("Failed to decrypt PiPiADS key for user %s: %s", telegram_chat_id, exc)
        return None

    if not api_key:
        return None
    return PiPiAdsAdapter(api_key=api_key)
