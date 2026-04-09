"""
Base class for all marketplace source integrations.

Every source (Amazon, Walmart, etc.) implements this interface
so the scanner and analyzer can work with any marketplace uniformly.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class ProductCondition(Enum):
    NEW = "new"
    USED = "used"
    REFURBISHED = "refurbished"
    UNKNOWN = "unknown"


class StockStatus(Enum):
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    UNKNOWN = "unknown"


@dataclass
class SourceProduct:
    """Standardized product data from any source marketplace."""

    # Identity
    source: str              # "amazon", "walmart", etc.
    source_id: str           # ASIN, Walmart ID, etc.
    url: str                 # Direct product URL

    # Product info
    title: str
    price: float
    currency: str = "USD"
    condition: ProductCondition = ProductCondition.NEW
    category: Optional[str] = None
    brand: Optional[str] = None
    image_url: Optional[str] = None
    upc: Optional[str] = None

    # Availability
    stock_status: StockStatus = StockStatus.UNKNOWN
    seller: Optional[str] = None
    ships_from: Optional[str] = None       # "US", "CN", etc.
    shipping_cost: float = 0.0
    estimated_delivery_days: Optional[int] = None

    # Ratings
    rating: Optional[float] = None         # 1-5
    review_count: Optional[int] = None

    # Metadata
    fetched_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def total_cost(self) -> float:
        """Total cost including shipping."""
        return round(self.price + self.shipping_cost, 2)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "source_id": self.source_id,
            "url": self.url,
            "title": self.title,
            "price": self.price,
            "currency": self.currency,
            "condition": self.condition.value,
            "category": self.category,
            "brand": self.brand,
            "image_url": self.image_url,
            "upc": self.upc,
            "stock_status": self.stock_status.value,
            "seller": self.seller,
            "ships_from": self.ships_from,
            "shipping_cost": self.shipping_cost,
            "estimated_delivery_days": self.estimated_delivery_days,
            "rating": self.rating,
            "review_count": self.review_count,
            "total_cost": self.total_cost,
            "fetched_at": self.fetched_at.isoformat(),
        }


class BaseSource(ABC):
    """
    Abstract base class for all marketplace sources.

    Subclasses must implement search() and get_product().
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Source name, e.g. 'amazon', 'walmart'."""
        ...

    @abstractmethod
    async def search(
        self,
        query: str,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 20,
    ) -> list[SourceProduct]:
        """
        Search for products by keyword.

        Args:
            query: Search keywords.
            category: Category filter (source-specific).
            min_price: Minimum price.
            max_price: Maximum price.
            limit: Max results.

        Returns:
            List of SourceProduct results.
        """
        ...

    @abstractmethod
    async def get_product(self, product_id: str) -> Optional[SourceProduct]:
        """
        Fetch a single product by its source-specific ID (ASIN, Walmart ID, etc.).

        Returns:
            SourceProduct or None if not found.
        """
        ...

    async def get_products(self, product_ids: list[str]) -> list[SourceProduct]:
        """
        Fetch multiple products by ID. Default: sequential calls.
        Override for batch API support.
        """
        results = []
        for pid in product_ids:
            product = await self.get_product(pid)
            if product:
                results.append(product)
        return results

    async def close(self):
        """Cleanup resources. Override if needed."""
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
