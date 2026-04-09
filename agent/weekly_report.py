"""
Weekly category report generation for DropAgent.

Builds a category-based report that blends marketplace opportunities with trend
signals so users can see which niches look promising for the coming week.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from agent.comparator import Opportunity, PriceComparator
from agent.trends import (
    DEFAULT_CATEGORY_KEYWORDS,
    GoogleTrendsScanner,
    RedditTrendResult,
    RedditTrendsScanner,
    TrendScanResult,
)
from i18n import t


DEFAULT_WEEKLY_REPORT_TITLE = "Weekly Category Report"


def classify_trend_direction(
    current_score: float,
    previous_score: Optional[float] = None,
    reddit_score: float = 0.0,
) -> str:
    """Classify a category trend as rising, stable, or declining."""
    if previous_score is not None:
        if current_score >= (previous_score * 1.2) + 5:
            return "rising"
        if current_score <= max(previous_score * 0.75, previous_score - 15):
            return "declining"
        return "stable"

    if current_score >= 80 or reddit_score >= 150:
        return "rising"
    if current_score >= 25 or reddit_score >= 60:
        return "stable"
    return "declining"


@dataclass
class WeeklyCategorySection:
    """One category block inside the weekly report."""

    category: str
    trend_direction: str
    google_top_score: float
    reddit_top_score: float
    top_keywords: list[str] = field(default_factory=list)
    opportunities: list[Opportunity] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.opportunities)

    @property
    def avg_profit(self) -> float:
        if not self.opportunities:
            return 0.0
        total = sum(item.margin.net_profit for item in self.opportunities)
        return round(total / len(self.opportunities), 2)

    @property
    def best_profit(self) -> float:
        if not self.opportunities:
            return 0.0
        return max(item.margin.net_profit for item in self.opportunities)

    @property
    def total_sold_count(self) -> int:
        return sum(item.ebay_sold_count for item in self.opportunities)

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "trend_direction": self.trend_direction,
            "google_top_score": self.google_top_score,
            "reddit_top_score": self.reddit_top_score,
            "top_keywords": list(self.top_keywords),
            "count": self.count,
            "avg_profit": self.avg_profit,
            "best_profit": self.best_profit,
            "total_sold_count": self.total_sold_count,
            "opportunities": [item.to_dict() for item in self.opportunities],
        }


@dataclass
class WeeklyCategoryReport:
    """Formatted weekly category report for Telegram, CLI, or dashboard."""

    title: str
    generated_at: datetime
    sections: list[WeeklyCategorySection] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.sections)

    def summary(self, lang: Optional[str] = None) -> str:
        """Human-readable summary."""
        sep = "=" * 60
        thin = "-" * 60

        if not self.sections:
            return f"{sep}\n  {t('weekly.no_categories', lang=lang)}\n{sep}"

        lines = [
            sep,
            f"  {t('weekly.title', lang=lang)}",
            f"  {t('weekly.generated_at', lang=lang)}: {self.generated_at.strftime('%Y-%m-%d %H:%M')}",
            f"  {t('weekly.report_for', lang=lang)}: {self.title}",
            sep,
        ]

        for section in self.sections:
            lines.append(
                f"  {section.category} | {t(f'weekly.direction_{section.trend_direction}', lang=lang)}"
            )
            lines.append(
                f"     {t('weekly.avg_profit', lang=lang)} ${section.avg_profit:.2f} | "
                f"{t('weekly.best_profit', lang=lang)} ${section.best_profit:.2f} | "
                f"{t('weekly.total_sold', lang=lang)} {section.total_sold_count}"
            )
            if section.top_keywords:
                lines.append(
                    f"     {t('weekly.top_keywords', lang=lang)}: {', '.join(section.top_keywords[:5])}"
                )
            for index, opportunity in enumerate(section.opportunities, start=1):
                lines.append(
                    f"     {index}. {opportunity.source_product.title[:40]} "
                    f"[{opportunity.source_product.source}] "
                    f"${opportunity.margin.net_profit:.2f}"
                )
            lines.append(thin)

        lines.append(sep)
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "generated_at": self.generated_at.isoformat(),
            "count": self.count,
            "sections": [section.to_dict() for section in self.sections],
        }


def build_weekly_category_report(
    category_opportunities: dict[str, list[Opportunity]],
    google_results: Optional[list[TrendScanResult]] = None,
    reddit_results: Optional[list[RedditTrendResult]] = None,
    previous_google_results: Optional[list[TrendScanResult]] = None,
    title: str = DEFAULT_WEEKLY_REPORT_TITLE,
    top_products: int = 5,
    generated_at: Optional[datetime] = None,
) -> WeeklyCategoryReport:
    """Build a weekly category report from opportunities and trend snapshots."""
    google_results = google_results or []
    reddit_results = reddit_results or []
    previous_google_results = previous_google_results or []

    google_by_category = {result.category: result for result in google_results}
    reddit_by_category = {result.category: result for result in reddit_results}
    previous_by_category = {result.category: result for result in previous_google_results}

    categories = set(category_opportunities)
    categories.update(google_by_category)
    categories.update(reddit_by_category)

    sections: list[WeeklyCategorySection] = []
    for category in sorted(categories):
        opportunities = sorted(
            category_opportunities.get(category, []),
            key=lambda item: item.score,
            reverse=True,
        )[:top_products]
        google_result = google_by_category.get(category)
        reddit_result = reddit_by_category.get(category)
        previous_google = previous_by_category.get(category)
        google_top_score = google_result.top_score if google_result else 0.0
        reddit_top_score = reddit_result.top_score if reddit_result else 0.0

        sections.append(
            WeeklyCategorySection(
                category=category,
                trend_direction=classify_trend_direction(
                    current_score=google_top_score,
                    previous_score=(previous_google.top_score if previous_google else None),
                    reddit_score=reddit_top_score,
                ),
                google_top_score=google_top_score,
                reddit_top_score=reddit_top_score,
                top_keywords=[keyword.keyword for keyword in (google_result.keywords if google_result else [])],
                opportunities=opportunities,
            )
        )

    sections.sort(
        key=lambda section: (section.best_profit, section.google_top_score, section.reddit_top_score),
        reverse=True,
    )
    return WeeklyCategoryReport(
        title=title,
        generated_at=generated_at or datetime.now(timezone.utc),
        sections=sections,
    )


class WeeklyCategoryReporter:
    """Generate a weekly report from category trend signals and opportunities."""

    def __init__(
        self,
        comparator: PriceComparator,
        google_scanner: Optional[GoogleTrendsScanner] = None,
        reddit_scanner: Optional[RedditTrendsScanner] = None,
        top_products: int = 5,
        trend_limit: int = 5,
        query_limit: int = 10,
    ):
        self.comparator = comparator
        self.google_scanner = google_scanner
        self.reddit_scanner = reddit_scanner
        self.top_products = top_products
        self.trend_limit = trend_limit
        self.query_limit = query_limit

    async def generate_report(
        self,
        categories: list[str],
        title: Optional[str] = None,
        generated_at: Optional[datetime] = None,
        previous_google_results: Optional[list[TrendScanResult]] = None,
    ) -> WeeklyCategoryReport:
        """Generate a weekly category report for the given categories."""
        if not categories:
            raise ValueError("At least one category is required")

        google_results = []
        if self.google_scanner is not None:
            google_results = self.google_scanner.scan_categories(
                categories=categories,
                limit=self.trend_limit,
            )

        reddit_results = []
        if self.reddit_scanner is not None:
            reddit_results = self.reddit_scanner.scan_categories(
                categories=categories,
                limit=self.trend_limit,
            )

        category_opportunities: dict[str, list[Opportunity]] = {}
        for category in categories:
            trend_keywords = []
            google_match = next((result for result in google_results if result.category == category), None)
            if google_match and google_match.keywords:
                trend_keywords = [item.keyword for item in google_match.keywords[: self.trend_limit]]
            else:
                trend_keywords = list(DEFAULT_CATEGORY_KEYWORDS.get(category, []))

            seen: dict[tuple[str, str], Opportunity] = {}
            if trend_keywords:
                tasks = [
                    self.comparator.find_opportunities(
                        query=keyword,
                        category=category,
                        limit=self.query_limit,
                    )
                    for keyword in trend_keywords
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if not isinstance(result, list):
                        continue
                    for opportunity in result:
                        key = (
                            opportunity.source_product.source,
                            opportunity.source_product.source_id,
                        )
                        current = seen.get(key)
                        if current is None or opportunity.score > current.score:
                            seen[key] = opportunity
            category_opportunities[category] = list(seen.values())

        return build_weekly_category_report(
            category_opportunities=category_opportunities,
            google_results=google_results,
            reddit_results=reddit_results,
            previous_google_results=previous_google_results,
            title=title or DEFAULT_WEEKLY_REPORT_TITLE,
            top_products=self.top_products,
            generated_at=generated_at,
        )
