"""
Daily digest generation for DropAgent.

Turns ranked marketplace opportunities into a morning report that can be sent
to Telegram or rendered in the dashboard.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from agent.comparator import Opportunity
from i18n import t


@dataclass
class DigestItem:
    """A single line item in the daily digest."""

    rank: int
    opportunity: Opportunity

    def to_dict(self) -> dict:
        return {
            "rank": self.rank,
            "score": self.opportunity.score,
            "source": self.opportunity.source_product.source,
            "title": self.opportunity.source_product.title,
            "buy_price": self.opportunity.source_product.price,
            "total_buy_cost": self.opportunity.source_product.total_cost,
            "ebay_avg_price": self.opportunity.ebay_avg_price,
            "ebay_sold_count": self.opportunity.ebay_sold_count,
            "net_profit": self.opportunity.margin.net_profit,
            "margin_percent": self.opportunity.margin.margin_percent,
            "keepa_insight": (
                self.opportunity.keepa_insight.to_dict()
                if self.opportunity.keepa_insight
                else None
            ),
        }


@dataclass
class DailyDigest:
    """Morning digest report with ranked opportunities."""

    title: str
    generated_at: datetime
    items: list[DigestItem] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.items)

    @property
    def total_sold_count(self) -> int:
        return sum(item.opportunity.ebay_sold_count for item in self.items)

    @property
    def avg_profit(self) -> float:
        if not self.items:
            return 0.0
        total = sum(item.opportunity.margin.net_profit for item in self.items)
        return round(total / len(self.items), 2)

    @property
    def best_profit(self) -> float:
        if not self.items:
            return 0.0
        return max(item.opportunity.margin.net_profit for item in self.items)

    def summary(self, lang: Optional[str] = None) -> str:
        """Human-readable digest for Telegram or CLI output."""
        sep = "=" * 60
        thin = "-" * 60

        if not self.items:
            return f"{sep}\n  {t('digest.no_opportunities', lang=lang)}\n{sep}"

        lines = [
            sep,
            f"  {t('digest.title', lang=lang)}",
            f"  {t('digest.generated_at', lang=lang)}: {self.generated_at.strftime('%Y-%m-%d %H:%M')}",
            f"  {t('digest.report_for', lang=lang)}: {self.title}",
            sep,
            f"  {t('digest.opportunities', lang=lang) + ':':<22}{self.count}",
            f"  {t('digest.avg_profit', lang=lang) + ':':<22}${self.avg_profit:.2f}",
            f"  {t('digest.best_profit', lang=lang) + ':':<22}${self.best_profit:.2f}",
            f"  {t('digest.total_sold', lang=lang) + ':':<22}{self.total_sold_count}",
            thin,
        ]

        for item in self.items:
            source = item.opportunity.source_product.source
            title = item.opportunity.source_product.title[:44]
            profit = item.opportunity.margin.net_profit
            margin = item.opportunity.margin.margin_percent
            buy_cost = item.opportunity.source_product.total_cost
            ebay_price = item.opportunity.ebay_avg_price
            score = item.opportunity.score
            lines.append(
                f"  {item.rank}. {title} [{source}]"
            )
            lines.append(
                f"     Buy ${buy_cost:.2f} -> eBay ${ebay_price:.2f} | "
                f"{t('calc.net_profit', lang=lang)} ${profit:.2f} | "
                f"{t('calc.margin', lang=lang)} {margin}% | "
                f"{t('digest.score', lang=lang)} {score}"
            )
            if item.opportunity.keepa_insight and item.opportunity.keepa_insight.avg_90d is not None:
                keepa = item.opportunity.keepa_insight
                keepa_line = f"     Keepa 90d avg ${keepa.avg_90d:.2f}"
                if keepa.current_price is not None:
                    keepa_line += f" | Now ${keepa.current_price:.2f}"
                if keepa.drops_90d:
                    keepa_line += f" | Drops 90d {keepa.drops_90d}"
                lines.append(keepa_line)

        lines.append(sep)
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "generated_at": self.generated_at.isoformat(),
            "count": self.count,
            "avg_profit": self.avg_profit,
            "best_profit": self.best_profit,
            "total_sold_count": self.total_sold_count,
            "items": [item.to_dict() for item in self.items],
        }


def build_daily_digest(
    opportunities: list[Opportunity],
    title: str = "Daily Opportunity Digest",
    top_n: int = 10,
    min_profit: float = 0.0,
    generated_at: Optional[datetime] = None,
) -> DailyDigest:
    """
    Build a ranked daily digest from opportunity data.

    Args:
        opportunities: Opportunities from the comparator layer.
        title: Report title or segment label.
        top_n: Maximum number of ranked opportunities to include.
        min_profit: Minimum net profit required to appear in the digest.
        generated_at: Report timestamp. Defaults to utcnow().

    Returns:
        DailyDigest object ready for formatting or serialization.
    """
    filtered = [
        opportunity
        for opportunity in opportunities
        if opportunity.margin.net_profit >= min_profit
    ]
    filtered.sort(key=lambda opportunity: opportunity.score, reverse=True)

    items = [
        DigestItem(rank=index, opportunity=opportunity)
        for index, opportunity in enumerate(filtered[:top_n], start=1)
    ]

    return DailyDigest(
        title=title,
        generated_at=generated_at or datetime.utcnow(),
        items=items,
    )
