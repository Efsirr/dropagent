"""
Price Comparator — connects sources, eBay scanner, and margin calculator.

This is the core engine that:
1. Takes a product query
2. Fetches prices from source marketplaces (Amazon, Walmart)
3. Checks eBay sold prices for the same product
4. Calculates margins for each source→eBay opportunity
5. Returns ranked results

This module powers the daily digest and real-time alerts.
"""

import asyncio
from dataclasses import dataclass
from typing import Optional

from agent.analyzer import BusinessModel, MarginResult, calculate_margin
from agent.scanner import EbayScanner, ScanResult
from agent.sources.base import BaseSource, SourceProduct
from i18n import t


@dataclass
class Opportunity:
    """A profitable product opportunity: source product + eBay data + margin."""

    source_product: SourceProduct
    ebay_avg_price: float
    ebay_sold_count: int
    margin: MarginResult

    @property
    def score(self) -> float:
        """
        Opportunity score — higher is better.
        Factors: profit, margin %, sales velocity.
        """
        profit_score = max(self.margin.net_profit, 0)
        margin_score = max(self.margin.margin_percent, 0) / 100
        velocity_score = min(self.ebay_sold_count / 10, 1.0)  # Normalize to 0-1
        return round(profit_score * (1 + margin_score) * (1 + velocity_score), 2)

    def summary(self, lang: Optional[str] = None) -> str:
        """One-line summary for listings."""
        return (
            f"${self.source_product.price:.2f} ({self.source_product.source}) → "
            f"${self.ebay_avg_price:.2f} (eBay) | "
            f"{t('calc.net_profit', lang=lang)}: ${self.margin.net_profit:.2f} | "
            f"{t('calc.margin', lang=lang)}: {self.margin.margin_percent}% | "
            f"Sold: {self.ebay_sold_count}"
        )

    def to_dict(self) -> dict:
        return {
            "source_product": self.source_product.to_dict(),
            "ebay_avg_price": self.ebay_avg_price,
            "ebay_sold_count": self.ebay_sold_count,
            "margin": self.margin.to_dict(),
            "score": self.score,
        }


class PriceComparator:
    """
    Finds profitable opportunities by comparing source prices to eBay sold data.
    """

    def __init__(
        self,
        sources: list[BaseSource],
        ebay_scanner: EbayScanner,
        business_model: BusinessModel = BusinessModel.US_ARBITRAGE,
        min_profit: float = 5.0,
        min_sold_count: int = 3,
    ):
        """
        Args:
            sources: List of marketplace sources to check prices from.
            ebay_scanner: Scanner for eBay sold listings data.
            business_model: US_ARBITRAGE or CHINA_DROPSHIPPING.
            min_profit: Minimum net profit to include in results ($).
            min_sold_count: Minimum eBay sold count to validate demand.
        """
        self.sources = sources
        self.ebay_scanner = ebay_scanner
        self.business_model = business_model
        self.min_profit = min_profit
        self.min_sold_count = min_sold_count

    async def find_opportunities(
        self,
        query: str,
        category: Optional[str] = None,
        max_buy_price: Optional[float] = None,
        limit: int = 20,
    ) -> list[Opportunity]:
        """
        Search all sources for a product and compare to eBay prices.

        Args:
            query: Product search term.
            category: Category filter.
            max_buy_price: Maximum buy price to consider.
            limit: Max products per source.

        Returns:
            List of Opportunity, sorted by score (best first).
        """
        # Step 1: Search all sources in parallel
        source_tasks = [
            source.search(
                query=query,
                category=category,
                max_price=max_buy_price,
                limit=limit,
            )
            for source in self.sources
        ]

        source_results = await asyncio.gather(*source_tasks, return_exceptions=True)

        # Flatten results, skip failed sources
        all_products: list[SourceProduct] = []
        for result in source_results:
            if isinstance(result, list):
                all_products.extend(result)

        if not all_products:
            return []

        # Step 2: Get eBay sold data for the query
        ebay_result = await self.ebay_scanner.search_sold(
            query=query,
            limit=50,
        )

        if ebay_result.count < self.min_sold_count:
            return []  # Not enough sales data to validate

        # Step 3: Calculate margins for each source product vs eBay avg price
        opportunities = []
        for product in all_products:
            margin = calculate_margin(
                buy_price=product.price,
                sell_price=ebay_result.avg_price,
                shipping_cost=product.shipping_cost,
                business_model=self.business_model,
                platform="ebay",
            )

            if margin.net_profit >= self.min_profit:
                opp = Opportunity(
                    source_product=product,
                    ebay_avg_price=ebay_result.avg_price,
                    ebay_sold_count=ebay_result.total_found,
                    margin=margin,
                )
                opportunities.append(opp)

        # Sort by score (best opportunities first)
        opportunities.sort(key=lambda o: o.score, reverse=True)
        return opportunities

    async def compare_product(
        self,
        product: SourceProduct,
        ebay_query: Optional[str] = None,
    ) -> Optional[Opportunity]:
        """
        Compare a single source product against eBay sold data.

        Args:
            product: Source product to evaluate.
            ebay_query: Custom eBay search query. Defaults to product title.

        Returns:
            Opportunity if profitable, None otherwise.
        """
        search_query = ebay_query or product.title

        ebay_result = await self.ebay_scanner.search_sold(
            query=search_query,
            limit=30,
        )

        if ebay_result.count < self.min_sold_count:
            return None

        margin = calculate_margin(
            buy_price=product.price,
            sell_price=ebay_result.avg_price,
            shipping_cost=product.shipping_cost,
            business_model=self.business_model,
            platform="ebay",
        )

        if margin.net_profit < self.min_profit:
            return None

        return Opportunity(
            source_product=product,
            ebay_avg_price=ebay_result.avg_price,
            ebay_sold_count=ebay_result.total_found,
            margin=margin,
        )

    async def close(self):
        """Close all source clients and scanner."""
        close_tasks = [source.close() for source in self.sources]
        close_tasks.append(self.ebay_scanner.close())
        await asyncio.gather(*close_tasks, return_exceptions=True)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
