"""
Margin Calculator & Product Analyzer for DropAgent.

Calculates net profit and margin percentage after all fees:
- eBay final value fee (13%)
- Payment processing (2.9% + $0.30)
- Shipping cost
- Packaging cost

Supports two business models:
  Model 1 — US Retail Arbitrage (Amazon/Walmart → eBay)
  Model 2 — China Dropshipping (AliExpress/CJ → eBay/Shopify)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from i18n import t


class BusinessModel(Enum):
    US_ARBITRAGE = "us_arbitrage"
    CHINA_DROPSHIPPING = "china_dropshipping"


# Default fee rates
EBAY_FEE_RATE = 0.13          # 13% final value fee
PAYMENT_PROCESSING_RATE = 0.029  # 2.9% managed payments
PAYMENT_FIXED_FEE = 0.30      # $0.30 per transaction
SHOPIFY_PROCESSING_RATE = 0.029  # 2.9% + $0.30
SHOPIFY_FIXED_FEE = 0.30

# Default cost estimates
DEFAULT_SHIPPING_COST = 5.00   # USD, domestic
DEFAULT_PACKAGING_COST = 1.50  # USD
DEFAULT_INTL_SHIPPING = 0.00   # ePacket/CJ often free for China model


@dataclass
class MarginResult:
    """Full breakdown of a margin calculation."""

    # Inputs
    buy_price: float
    sell_price: float
    shipping_cost: float
    packaging_cost: float
    business_model: BusinessModel
    platform: str  # "ebay" or "shopify"

    # Calculated fees
    platform_fee: float = 0.0
    payment_fee: float = 0.0
    total_fees: float = 0.0
    total_cost: float = 0.0

    # Results
    net_profit: float = 0.0
    margin_percent: float = 0.0
    roi_percent: float = 0.0
    markup: float = 0.0

    def __post_init__(self):
        self._calculate()

    def _calculate(self):
        # Platform fee (percentage of sell price)
        if self.platform == "ebay":
            self.platform_fee = round(self.sell_price * EBAY_FEE_RATE, 2)
        else:
            self.platform_fee = 0.0  # Shopify charges subscription, not per-item

        # Payment processing fee
        self.payment_fee = round(
            self.sell_price * PAYMENT_PROCESSING_RATE + PAYMENT_FIXED_FEE, 2
        )

        # Totals
        self.total_fees = round(self.platform_fee + self.payment_fee, 2)
        self.total_cost = round(
            self.buy_price + self.shipping_cost + self.packaging_cost + self.total_fees,
            2,
        )
        self.net_profit = round(self.sell_price - self.total_cost, 2)

        # Percentages
        if self.sell_price > 0:
            self.margin_percent = round((self.net_profit / self.sell_price) * 100, 2)
        if self.buy_price > 0:
            self.roi_percent = round((self.net_profit / self.buy_price) * 100, 2)
            self.markup = round(self.sell_price / self.buy_price, 2)

    @property
    def is_profitable(self) -> bool:
        return self.net_profit > 0

    def summary(self, lang: Optional[str] = None) -> str:
        """Human-readable summary for Telegram/CLI output."""
        status = t("calc.profit", lang=lang) if self.is_profitable else t("calc.loss", lang=lang)
        sep = "=" * 40
        thin = "─" * 40
        lines = [
            sep,
            f"  {t('calc.title', lang=lang)} — {status}",
            sep,
            f"  {t('calc.buy_price', lang=lang) + ':':<20}${self.buy_price:.2f}",
            f"  {t('calc.sell_price', lang=lang) + ':':<20}${self.sell_price:.2f}",
            thin,
            f"  {t('calc.shipping', lang=lang) + ':':<20}${self.shipping_cost:.2f}",
            f"  {t('calc.packaging', lang=lang) + ':':<20}${self.packaging_cost:.2f}",
            f"  {t('calc.platform_fee', lang=lang) + ':':<20}${self.platform_fee:.2f}  ({self.platform})",
            f"  {t('calc.payment_fee', lang=lang) + ':':<20}${self.payment_fee:.2f}",
            thin,
            f"  {t('calc.total_fees', lang=lang) + ':':<20}${self.total_fees:.2f}",
            f"  {t('calc.total_cost', lang=lang) + ':':<20}${self.total_cost:.2f}",
            thin,
            f"  {t('calc.net_profit', lang=lang) + ':':<20}${self.net_profit:.2f}",
            f"  {t('calc.margin', lang=lang) + ':':<20}{self.margin_percent}%",
            f"  {t('calc.roi', lang=lang) + ':':<20}{self.roi_percent}%",
            f"  {t('calc.markup', lang=lang) + ':':<20}{self.markup}x",
            sep,
        ]
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Dict representation for API responses."""
        return {
            "buy_price": self.buy_price,
            "sell_price": self.sell_price,
            "shipping_cost": self.shipping_cost,
            "packaging_cost": self.packaging_cost,
            "business_model": self.business_model.value,
            "platform": self.platform,
            "platform_fee": self.platform_fee,
            "payment_fee": self.payment_fee,
            "total_fees": self.total_fees,
            "total_cost": self.total_cost,
            "net_profit": self.net_profit,
            "margin_percent": self.margin_percent,
            "roi_percent": self.roi_percent,
            "markup": self.markup,
            "is_profitable": self.is_profitable,
        }


def calculate_margin(
    buy_price: float,
    sell_price: float,
    shipping_cost: Optional[float] = None,
    packaging_cost: Optional[float] = None,
    business_model: BusinessModel = BusinessModel.US_ARBITRAGE,
    platform: str = "ebay",
) -> MarginResult:
    """
    Calculate profit margin for a product.

    Args:
        buy_price: Cost to purchase the product from source.
        sell_price: Expected or actual selling price.
        shipping_cost: Shipping cost (defaults based on business model).
        packaging_cost: Packaging cost (defaults to $1.50).
        business_model: US_ARBITRAGE or CHINA_DROPSHIPPING.
        platform: Selling platform — "ebay" or "shopify".

    Returns:
        MarginResult with full fee breakdown.
    """
    if buy_price < 0 or sell_price < 0:
        raise ValueError("Prices cannot be negative")

    # Set defaults based on business model
    if shipping_cost is None:
        if business_model == BusinessModel.CHINA_DROPSHIPPING:
            shipping_cost = DEFAULT_INTL_SHIPPING
        else:
            shipping_cost = DEFAULT_SHIPPING_COST

    if packaging_cost is None:
        packaging_cost = DEFAULT_PACKAGING_COST

    return MarginResult(
        buy_price=buy_price,
        sell_price=sell_price,
        shipping_cost=shipping_cost,
        packaging_cost=packaging_cost,
        business_model=business_model,
        platform=platform,
    )


def batch_calculate(
    products: list[dict],
    business_model: BusinessModel = BusinessModel.US_ARBITRAGE,
    platform: str = "ebay",
    min_profit: float = 0.0,
) -> list[MarginResult]:
    """
    Calculate margins for multiple products, optionally filtering by min profit.

    Args:
        products: List of dicts with "buy_price" and "sell_price" keys.
                  Optional: "shipping_cost", "packaging_cost", "name".
        business_model: Applied to all products.
        platform: Selling platform for all products.
        min_profit: Only return products with net_profit >= this value.

    Returns:
        List of MarginResult, sorted by net_profit descending.
    """
    results = []
    for product in products:
        result = calculate_margin(
            buy_price=product["buy_price"],
            sell_price=product["sell_price"],
            shipping_cost=product.get("shipping_cost"),
            packaging_cost=product.get("packaging_cost"),
            business_model=business_model,
            platform=platform,
        )
        if result.net_profit >= min_profit:
            results.append(result)

    results.sort(key=lambda r: r.net_profit, reverse=True)
    return results
