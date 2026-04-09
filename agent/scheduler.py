"""
Scheduling and orchestration utilities for DropAgent digests.

This module coordinates repeated marketplace scans and turns the resulting
opportunities into a single daily digest.
"""

import asyncio
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from agent.comparator import Opportunity, PriceComparator
from agent.digest import DailyDigest, build_daily_digest
from i18n import t


@dataclass
class ScanRequest:
    """A single configured marketplace search for the morning digest."""

    query: str
    category: Optional[str] = None
    max_buy_price: Optional[float] = None
    limit: int = 20


def load_scan_requests_from_env(env: Optional[dict] = None) -> list[ScanRequest]:
    """
    Load digest scan requests from environment configuration.

    DIGEST_QUERIES format:
        "airpods pro,gaming mouse,lego star wars"
    """
    env = env or os.environ
    raw = env.get("DIGEST_QUERIES", "").strip()
    if not raw:
        return []

    requests = []
    for query in raw.split(","):
        query = query.strip()
        if query:
            requests.append(ScanRequest(query=query))
    return requests


class MorningDigestScheduler:
    """Builds a morning digest from multiple configured scan requests."""

    def __init__(
        self,
        comparator: PriceComparator,
        top_n: int = 10,
        min_profit: float = 5.0,
    ):
        self.comparator = comparator
        self.top_n = top_n
        self.min_profit = min_profit

    async def generate_digest(
        self,
        requests: list[ScanRequest],
        title: Optional[str] = None,
        generated_at: Optional[datetime] = None,
    ) -> DailyDigest:
        """
        Run all configured scans and return a single ranked digest.

        Results are deduplicated by source marketplace and source product ID.
        """
        if not requests:
            return build_daily_digest(
                [],
                title=title or t("digest.default_report_title"),
                top_n=self.top_n,
                min_profit=self.min_profit,
                generated_at=generated_at,
            )

        tasks = [
            self.comparator.find_opportunities(
                query=request.query,
                category=request.category,
                max_buy_price=request.max_buy_price,
                limit=request.limit,
            )
            for request in requests
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        deduped: dict[tuple[str, str], Opportunity] = {}
        for result in results:
            if not isinstance(result, list):
                continue
            for opportunity in result:
                key = (
                    opportunity.source_product.source,
                    opportunity.source_product.source_id,
                )
                current = deduped.get(key)
                if current is None or opportunity.score > current.score:
                    deduped[key] = opportunity

        return build_daily_digest(
            list(deduped.values()),
            title=title or t("digest.default_report_title"),
            top_n=self.top_n,
            min_profit=self.min_profit,
            generated_at=generated_at,
        )
