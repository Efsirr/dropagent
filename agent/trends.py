"""
Google Trends scanner for DropAgent.

This module surfaces rising search terms by category so the digest and alert
systems can spot demand before marketplace listings saturate.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from i18n import t

try:
    from pytrends.request import TrendReq
except ImportError:  # pragma: no cover - exercised via tests with fallback path
    TrendReq = None

try:
    import praw
except ImportError:  # pragma: no cover - exercised via tests with fallback path
    praw = None


DEFAULT_TREND_GEO = "US"
DEFAULT_TREND_TIMEFRAME = "now 7-d"
DEFAULT_TREND_LIMIT = 10
DEFAULT_REDDIT_LIMIT = 10
DEFAULT_CATEGORY_KEYWORDS = {
    "electronics": ["airpods", "gaming mouse", "wireless earbuds"],
    "toys": ["lego", "pokemon cards", "hot wheels"],
    "home": ["air fryer", "robot vacuum", "standing desk"],
    "gaming": ["nintendo switch", "ps5 accessories", "gaming headset"],
}
DEFAULT_REDDIT_SUBREDDITS = {
    "electronics": ["buildapcsales", "gadgets", "headphones"],
    "toys": ["lego", "pokemoncards", "toys"],
    "home": ["homeimprovement", "buyitforlife", "frugal"],
    "gaming": ["nintendoswitch", "ps5", "gaming"],
}


@dataclass
class TrendKeyword:
    """Single keyword returned from Google Trends."""

    keyword: str
    score: float
    category: Optional[str] = None
    source: str = "google_trends"

    def to_dict(self) -> dict:
        return {
            "keyword": self.keyword,
            "score": self.score,
            "category": self.category,
            "source": self.source,
        }


@dataclass
class TrendScanResult:
    """Aggregated trend results for one category/query group."""

    category: str
    keywords: list[TrendKeyword]
    generated_at: datetime
    source: str = "google_trends"

    @property
    def count(self) -> int:
        return len(self.keywords)

    @property
    def top_score(self) -> float:
        if not self.keywords:
            return 0.0
        return max(keyword.score for keyword in self.keywords)

    def summary(self, lang: Optional[str] = None) -> str:
        """Human-readable summary for CLI, bot, or dashboard previews."""
        sep = "=" * 50
        if not self.keywords:
            return f"{sep}\n  {t('trends.no_results', lang=lang, category=self.category)}\n{sep}"

        lines = [
            sep,
            f"  {t('trends.title', lang=lang)}",
            f"  {t('trends.category', lang=lang)}: {self.category}",
            f"  {t('trends.generated_at', lang=lang)}: {self.generated_at.strftime('%Y-%m-%d %H:%M')}",
            sep,
        ]
        for index, keyword in enumerate(self.keywords, start=1):
            lines.append(
                f"  {index}. {keyword.keyword} — {t('trends.score', lang=lang)}: {keyword.score}"
            )
        lines.append(sep)
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "count": self.count,
            "top_score": self.top_score,
            "generated_at": self.generated_at.isoformat(),
            "source": self.source,
            "keywords": [keyword.to_dict() for keyword in self.keywords],
        }


@dataclass
class RedditTrendSignal:
    """Single hype signal extracted from Reddit."""

    title: str
    subreddit: str
    score: float
    url: str
    keyword: Optional[str] = None
    source: str = "reddit"

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "subreddit": self.subreddit,
            "score": self.score,
            "url": self.url,
            "keyword": self.keyword,
            "source": self.source,
        }


@dataclass
class RedditTrendResult:
    """Aggregated Reddit trend signals for one category."""

    category: str
    signals: list[RedditTrendSignal]
    generated_at: datetime
    source: str = "reddit"

    @property
    def count(self) -> int:
        return len(self.signals)

    @property
    def top_score(self) -> float:
        if not self.signals:
            return 0.0
        return max(signal.score for signal in self.signals)

    def summary(self, lang: Optional[str] = None) -> str:
        sep = "=" * 50
        if not self.signals:
            return f"{sep}\n  {t('reddit.no_results', lang=lang, category=self.category)}\n{sep}"

        lines = [
            sep,
            f"  {t('reddit.title', lang=lang)}",
            f"  {t('reddit.category', lang=lang)}: {self.category}",
            f"  {t('reddit.generated_at', lang=lang)}: {self.generated_at.strftime('%Y-%m-%d %H:%M')}",
            sep,
        ]
        for index, signal in enumerate(self.signals, start=1):
            lines.append(
                f"  {index}. r/{signal.subreddit} — {signal.title[:48]} ({t('reddit.score', lang=lang)}: {signal.score})"
            )
        lines.append(sep)
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "count": self.count,
            "top_score": self.top_score,
            "generated_at": self.generated_at.isoformat(),
            "source": self.source,
            "signals": [signal.to_dict() for signal in self.signals],
        }


class GoogleTrendsScanner:
    """Thin wrapper around pytrends with test-friendly injection points."""

    def __init__(
        self,
        client: Optional[Any] = None,
        hl: str = "en-US",
        tz: int = 0,
        geo: str = DEFAULT_TREND_GEO,
        timeframe: str = DEFAULT_TREND_TIMEFRAME,
    ):
        self._client = client
        self._hl = hl
        self._tz = tz
        self._geo = geo
        self._timeframe = timeframe
        self._category_keywords = dict(DEFAULT_CATEGORY_KEYWORDS)

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        if TrendReq is None:
            raise ValueError(
                "pytrends is required for Google Trends scanning. Install pytrends to use GoogleTrendsScanner."
            )
        self._client = TrendReq(hl=self._hl, tz=self._tz)
        return self._client

    def scan_category(
        self,
        category: str,
        keywords: list[str],
        geo: Optional[str] = None,
        timeframe: Optional[str] = None,
        limit: int = DEFAULT_TREND_LIMIT,
    ) -> TrendScanResult:
        """
        Scan Google Trends for related rising queries in a category.

        Args:
            category: Friendly category label, e.g. "electronics".
            keywords: Seed keywords for Google Trends.
            geo: Region code, defaults to US.
            timeframe: Trend timeframe, defaults to last 7 days.
            limit: Max rising queries to return.
        """
        if not keywords:
            raise ValueError("At least one keyword is required")

        client = self._get_client()
        client.build_payload(
            keywords,
            cat=0,
            timeframe=timeframe or self._timeframe,
            geo=geo or self._geo,
        )
        related_queries = client.related_queries()

        rising_rows = []
        for seed_keyword in keywords:
            keyword_data = related_queries.get(seed_keyword, {})
            rising_rows.extend(keyword_data.get("rising", []) or [])

        deduped: dict[str, TrendKeyword] = {}
        for row in rising_rows:
            title = row.get("query")
            if not title:
                continue
            value = row.get("value", 0)
            try:
                score = float(value)
            except (TypeError, ValueError):
                continue

            current = deduped.get(title)
            trend_keyword = TrendKeyword(keyword=title, score=score, category=category)
            if current is None or trend_keyword.score > current.score:
                deduped[title] = trend_keyword

        ranked_keywords = sorted(
            deduped.values(),
            key=lambda keyword: keyword.score,
            reverse=True,
        )[:limit]

        return TrendScanResult(
            category=category,
            keywords=ranked_keywords,
            generated_at=datetime.now(timezone.utc),
        )

    def category_keywords(self, category: str) -> list[str]:
        """Return configured seed keywords for a category."""
        keywords = self._category_keywords.get(category.lower())
        if not keywords:
            raise ValueError(f"Unknown category: {category}")
        return list(keywords)

    def scan_configured_category(
        self,
        category: str,
        geo: Optional[str] = None,
        timeframe: Optional[str] = None,
        limit: int = DEFAULT_TREND_LIMIT,
    ) -> TrendScanResult:
        """Scan one configured category using its default keywords."""
        return self.scan_category(
            category=category,
            keywords=self.category_keywords(category),
            geo=geo,
            timeframe=timeframe,
            limit=limit,
        )

    def scan_categories(
        self,
        categories: list[str],
        geo: Optional[str] = None,
        timeframe: Optional[str] = None,
        limit: int = DEFAULT_TREND_LIMIT,
    ) -> list[TrendScanResult]:
        """Scan multiple configured categories and return one result per category."""
        if not categories:
            raise ValueError("At least one category is required")

        results = []
        for category in categories:
            results.append(
                self.scan_configured_category(
                    category=category,
                    geo=geo,
                    timeframe=timeframe,
                    limit=limit,
                )
            )
        return results


def merge_trend_results(results: list[TrendScanResult], limit: int = DEFAULT_TREND_LIMIT) -> TrendScanResult:
    """Merge multiple category scans into one ranked combined result."""
    if not results:
        raise ValueError("At least one trend result is required")

    deduped: "OrderedDict[str, TrendKeyword]" = OrderedDict()
    for result in results:
        for keyword in result.keywords:
            current = deduped.get(keyword.keyword)
            if current is None or keyword.score > current.score:
                deduped[keyword.keyword] = TrendKeyword(
                    keyword=keyword.keyword,
                    score=keyword.score,
                    category=keyword.category,
                )

    merged_keywords = sorted(
        deduped.values(),
        key=lambda keyword: keyword.score,
        reverse=True,
    )[:limit]

    return TrendScanResult(
        category="combined",
        keywords=merged_keywords,
        generated_at=max(result.generated_at for result in results),
    )


class RedditTrendsScanner:
    """Collect Reddit hype signals across configured subreddits."""

    def __init__(
        self,
        client: Optional[Any] = None,
        subreddits_by_category: Optional[dict[str, list[str]]] = None,
    ):
        self._client = client
        self._subreddits_by_category = dict(DEFAULT_REDDIT_SUBREDDITS)
        if subreddits_by_category:
            self._subreddits_by_category.update(subreddits_by_category)

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        if praw is None:
            raise ValueError(
                "praw is required for Reddit scanning. Install praw to use RedditTrendsScanner."
            )
        raise ValueError(
            "RedditTrendsScanner requires an initialized Reddit client. Inject a configured praw.Reddit instance."
        )

    def category_subreddits(self, category: str) -> list[str]:
        subreddits = self._subreddits_by_category.get(category.lower())
        if not subreddits:
            raise ValueError(f"Unknown category: {category}")
        return list(subreddits)

    def score_post(self, post: Any) -> float:
        """Convert Reddit engagement into a simple hype score."""
        score = float(getattr(post, "score", 0) or 0)
        comments = float(getattr(post, "num_comments", 0) or 0)
        upvote_ratio = float(getattr(post, "upvote_ratio", 0) or 0)
        awards = float(getattr(post, "total_awards_received", 0) or 0)
        return round(score + comments * 2 + upvote_ratio * 100 + awards * 25, 2)

    def scan_category(
        self,
        category: str,
        keywords: Optional[list[str]] = None,
        subreddits: Optional[list[str]] = None,
        limit: int = DEFAULT_REDDIT_LIMIT,
        sort: str = "hot",
    ) -> RedditTrendResult:
        """Scan configured subreddits for hype signals relevant to the category."""
        client = self._get_client()
        target_subreddits = subreddits or self.category_subreddits(category)
        keyword_filters = [keyword.lower() for keyword in (keywords or [])]

        signals = []
        for subreddit_name in target_subreddits:
            subreddit = client.subreddit(subreddit_name)
            posts = getattr(subreddit, sort)(limit=limit)
            for post in posts:
                title = getattr(post, "title", "")
                lowered_title = title.lower()
                if keyword_filters and not any(keyword in lowered_title for keyword in keyword_filters):
                    continue

                matched_keyword = None
                for keyword in keyword_filters:
                    if keyword in lowered_title:
                        matched_keyword = keyword
                        break

                signals.append(
                    RedditTrendSignal(
                        title=title,
                        subreddit=subreddit_name,
                        score=self.score_post(post),
                        url=getattr(post, "url", ""),
                        keyword=matched_keyword,
                    )
                )

        ranked_signals = sorted(signals, key=lambda signal: signal.score, reverse=True)[:limit]
        return RedditTrendResult(
            category=category,
            signals=ranked_signals,
            generated_at=datetime.now(timezone.utc),
        )
