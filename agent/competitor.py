"""
Competitor tracker for monitoring specific eBay sellers.

This module scans sold listings by seller, summarizes what is moving, and
highlights newly observed items since the last scan.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from agent.scanner import EbayScanner, ScanResult, SoldItem
from i18n import t


@dataclass
class CompetitorItem:
    """Observed sold listing for a competitor seller."""

    item_id: str
    title: str
    sold_price: float
    sold_date: Optional[datetime]
    category: Optional[str] = None
    is_new: bool = False

    def to_dict(self) -> dict:
        return {
            "item_id": self.item_id,
            "title": self.title,
            "sold_price": self.sold_price,
            "sold_date": self.sold_date.isoformat() if self.sold_date else None,
            "category": self.category,
            "is_new": self.is_new,
        }


@dataclass
class CompetitorReport:
    """Summary of a competitor seller scan."""

    seller_username: str
    generated_at: datetime
    items: list[CompetitorItem] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.items)

    @property
    def new_count(self) -> int:
        return sum(1 for item in self.items if item.is_new)

    @property
    def avg_sold_price(self) -> float:
        if not self.items:
            return 0.0
        return round(sum(item.sold_price for item in self.items) / len(self.items), 2)

    @property
    def top_categories(self) -> list[str]:
        categories = [item.category for item in self.items if item.category]
        return [name for name, _ in Counter(categories).most_common(3)]

    def summary(self, lang: Optional[str] = None) -> str:
        sep = "=" * 60
        if not self.items:
            return (
                f"{sep}\n"
                f"  {t('competitor.title', lang=lang)}\n"
                f"  {t('competitor.no_results', lang=lang, seller=self.seller_username)}\n"
                f"{sep}"
            )

        lines = [
            sep,
            f"  {t('competitor.title', lang=lang)}",
            f"  {t('competitor.seller', lang=lang)}: {self.seller_username}",
            f"  {t('competitor.generated_at', lang=lang)}: {self.generated_at.strftime('%Y-%m-%d %H:%M')}",
            sep,
            f"  {t('competitor.total_items', lang=lang)}: {self.count}",
            f"  {t('competitor.new_items', lang=lang)}: {self.new_count}",
            f"  {t('competitor.avg_price', lang=lang)}: ${self.avg_sold_price:.2f}",
        ]
        if self.top_categories:
            lines.append(f"  {t('competitor.top_categories', lang=lang)}: {', '.join(self.top_categories)}")
        lines.append("-" * 60)
        for index, item in enumerate(self.items[:8], start=1):
            new_suffix = f" [{t('competitor.new_badge', lang=lang)}]" if item.is_new else ""
            lines.append(
                f"  {index}. ${item.sold_price:.2f} — {item.title[:42]}{new_suffix}"
            )
        lines.append(sep)
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "seller_username": self.seller_username,
            "generated_at": self.generated_at.isoformat(),
            "count": self.count,
            "new_count": self.new_count,
            "avg_sold_price": self.avg_sold_price,
            "top_categories": list(self.top_categories),
            "items": [item.to_dict() for item in self.items],
        }


class CompetitorTracker:
    """Seller-focused tracker built on top of the eBay sold scanner."""

    def __init__(self, ebay_scanner: EbayScanner):
        self.ebay_scanner = ebay_scanner

    async def scan_seller(
        self,
        seller_username: str,
        known_item_ids: Optional[set[str]] = None,
        query: Optional[str] = None,
        limit: int = 25,
    ) -> CompetitorReport:
        """Scan sold listings for a seller and mark newly observed items."""
        seller_username = seller_username.strip()
        if not seller_username:
            raise ValueError("seller_username is required")

        known_item_ids = known_item_ids or set()
        search_query = query.strip() if query else "*"
        result: ScanResult = await self.ebay_scanner.search_sold(
            query=search_query,
            seller=seller_username,
            limit=limit,
        )

        items = [
            CompetitorItem(
                item_id=item.item_id,
                title=item.title,
                sold_price=item.sold_price,
                sold_date=item.sold_date,
                category=item.category,
                is_new=item.item_id not in known_item_ids,
            )
            for item in result.items
        ]
        return CompetitorReport(
            seller_username=seller_username,
            generated_at=datetime.now(timezone.utc),
            items=items,
        )
