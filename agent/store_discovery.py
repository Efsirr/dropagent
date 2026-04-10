"""Store discovery reports built on top of StoreLeads data."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from agent.adapters.storeleads import StoreDomain
from i18n import t


@dataclass
class StoreDiscoveryReport:
    """Simple report for competitor store discovery."""

    query: str
    generated_at: datetime
    stores: list[StoreDomain] = field(default_factory=list)
    platform: str = "shopify"
    country: Optional[str] = None

    @property
    def count(self) -> int:
        return len(self.stores)

    def summary(self, lang: Optional[str] = None) -> str:
        sep = "=" * 60
        if not self.stores:
            return (
                f"{sep}\n"
                f"  {t('discovery.title', lang=lang)}\n"
                f"  {t('discovery.no_results', lang=lang, query=self.query)}\n"
                f"{sep}"
            )

        lines = [
            sep,
            f"  {t('discovery.title', lang=lang)}",
            f"  {t('discovery.query', lang=lang)}: {self.query}",
            f"  {t('discovery.generated_at', lang=lang)}: {self.generated_at.strftime('%Y-%m-%d %H:%M')}",
            f"  {t('discovery.platform', lang=lang)}: {self.platform}",
            sep,
            f"  {t('discovery.total_stores', lang=lang)}: {self.count}",
            "-" * 60,
        ]

        for index, store in enumerate(self.stores[:8], start=1):
            visits = (
                f" | {t('discovery.visits', lang=lang)} {store.estimated_visits}"
                if store.estimated_visits
                else ""
            )
            sales = (
                f" | {t('discovery.sales', lang=lang)} ${store.estimated_sales_monthly_usd:.0f}"
                if store.estimated_sales_monthly_usd
                else ""
            )
            avg_price = (
                f" | {t('discovery.avg_price', lang=lang)} ${store.avg_price_usd:.2f}"
                if store.avg_price_usd is not None
                else ""
            )
            label = store.merchant_name or store.domain
            lines.append(f"  {index}. {label} ({store.domain}){visits}{sales}{avg_price}")

        lines.append(sep)
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "generated_at": self.generated_at.isoformat(),
            "platform": self.platform,
            "country": self.country,
            "count": self.count,
            "stores": [store.to_dict() for store in self.stores],
        }


def build_store_discovery_report(
    query: str,
    stores: list[StoreDomain],
    platform: str = "shopify",
    country: Optional[str] = None,
    generated_at: Optional[datetime] = None,
) -> StoreDiscoveryReport:
    """Build a StoreDiscoveryReport from StoreLeads results."""
    return StoreDiscoveryReport(
        query=query,
        generated_at=generated_at or datetime.now(timezone.utc),
        stores=stores,
        platform=platform,
        country=country,
    )
