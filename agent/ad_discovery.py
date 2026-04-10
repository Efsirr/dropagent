"""Ad discovery reports built on top of PiPiADS results."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from agent.adapters.pipiads import TikTokAd
from i18n import t


@dataclass
class AdDiscoveryReport:
    """Simple report for TikTok ad discovery."""

    query: str
    generated_at: datetime
    ads: list[TikTokAd] = field(default_factory=list)
    country: Optional[str] = None

    @property
    def count(self) -> int:
        return len(self.ads)

    def summary(self, lang: Optional[str] = None) -> str:
        sep = "=" * 60
        if not self.ads:
            return (
                f"{sep}\n"
                f"  {t('ad_discovery.title', lang=lang)}\n"
                f"  {t('ad_discovery.no_results', lang=lang, query=self.query)}\n"
                f"{sep}"
            )

        lines = [
            sep,
            f"  {t('ad_discovery.title', lang=lang)}",
            f"  {t('ad_discovery.query', lang=lang)}: {self.query}",
            f"  {t('ad_discovery.generated_at', lang=lang)}: {self.generated_at.strftime('%Y-%m-%d %H:%M')}",
            sep,
            f"  {t('ad_discovery.total_ads', lang=lang)}: {self.count}",
            "-" * 60,
        ]
        for index, ad in enumerate(self.ads[:8], start=1):
            likes = f"{t('ad_discovery.likes', lang=lang)} {ad.total_likes}"
            shares = f"{t('ad_discovery.shares', lang=lang)} {ad.total_shares}"
            days = f"{t('ad_discovery.days', lang=lang)} {ad.days_running}"
            score = f"{t('ad_discovery.score', lang=lang)} {ad.trend_score}"
            advertiser = f" [{ad.advertiser}]" if ad.advertiser else ""
            title = (ad.title or "Untitled ad")[:40]
            lines.append(f"  {index}. {title}{advertiser} | {likes} | {shares} | {days} | {score}")
        lines.append(sep)
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "generated_at": self.generated_at.isoformat(),
            "count": self.count,
            "country": self.country,
            "ads": [ad.to_dict() for ad in self.ads],
        }


def build_ad_discovery_report(
    query: str,
    ads: list[TikTokAd],
    country: Optional[str] = None,
    generated_at: Optional[datetime] = None,
) -> AdDiscoveryReport:
    """Build an AdDiscoveryReport from PiPiADS results."""
    return AdDiscoveryReport(
        query=query,
        generated_at=generated_at or datetime.now(timezone.utc),
        ads=ads,
        country=country,
    )
