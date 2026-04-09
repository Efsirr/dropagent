"""Telegram-style handler for the /calc command."""

from typing import Optional

from agent.analyzer import BusinessModel, calculate_margin
from i18n import t


def handle_calc_command(text: str, lang: Optional[str] = None) -> str:
    """
    Handle `/calc` command text.

    Expected format:
        /calc <buy_price> <sell_price> [shipping_cost] [packaging_cost]
    """
    parts = text.strip().split()

    if len(parts) < 3:
        return (
            "Usage: /calc <buy_price> <sell_price> [shipping_cost] [packaging_cost]\n"
            "Example: /calc 25 49.99 5 1.5"
        )

    try:
        buy_price = float(parts[1])
        sell_price = float(parts[2])
        shipping_cost = float(parts[3]) if len(parts) > 3 else None
        packaging_cost = float(parts[4]) if len(parts) > 4 else None
    except ValueError:
        return f"{t('common.error', lang=lang)}: invalid numeric values"

    try:
        result = calculate_margin(
            buy_price=buy_price,
            sell_price=sell_price,
            shipping_cost=shipping_cost,
            packaging_cost=packaging_cost,
            business_model=BusinessModel.US_ARBITRAGE,
            platform="ebay",
        )
        return result.summary(lang=lang)
    except ValueError as error:
        return f"{t('common.error', lang=lang)}: {error}"
