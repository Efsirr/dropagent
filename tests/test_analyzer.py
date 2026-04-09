"""Tests for the margin calculator."""

import pytest

from agent.analyzer import (
    BusinessModel,
    MarginResult,
    batch_calculate,
    calculate_margin,
)


class TestCalculateMargin:
    """Core margin calculation tests."""

    def test_basic_profitable_product(self):
        """US arbitrage: buy $25 on Amazon, sell $49.99 on eBay."""
        result = calculate_margin(buy_price=25.0, sell_price=49.99)

        assert result.is_profitable
        assert result.buy_price == 25.0
        assert result.sell_price == 49.99
        assert result.platform == "ebay"
        assert result.business_model == BusinessModel.US_ARBITRAGE

        # eBay fee: 49.99 * 0.13 = 6.50
        assert result.platform_fee == 6.50
        # Payment fee: 49.99 * 0.029 + 0.30 = 1.75
        assert result.payment_fee == 1.75
        # Total fees: 6.50 + 1.75 = 8.25
        assert result.total_fees == 8.25
        # Total cost: 25 + 5.00 (shipping) + 1.50 (packaging) + 8.25 = 39.75
        assert result.total_cost == 39.75
        # Net profit: 49.99 - 39.75 = 10.24
        assert result.net_profit == 10.24
        assert result.margin_percent > 0

    def test_unprofitable_product(self):
        """Product where fees eat all the margin."""
        result = calculate_margin(buy_price=45.0, sell_price=49.99)

        assert not result.is_profitable
        assert result.net_profit < 0

    def test_china_model_defaults(self):
        """China dropshipping: free shipping by default."""
        result = calculate_margin(
            buy_price=3.50,
            sell_price=24.99,
            business_model=BusinessModel.CHINA_DROPSHIPPING,
        )

        assert result.shipping_cost == 0.0  # Free ePacket
        assert result.is_profitable
        assert result.markup > 5  # Should be ~7x markup

    def test_custom_shipping_and_packaging(self):
        """Override default shipping and packaging costs."""
        result = calculate_margin(
            buy_price=30.0,
            sell_price=60.0,
            shipping_cost=10.0,
            packaging_cost=3.0,
        )

        assert result.shipping_cost == 10.0
        assert result.packaging_cost == 3.0

    def test_shopify_platform(self):
        """Shopify has no per-item platform fee."""
        result = calculate_margin(
            buy_price=5.0,
            sell_price=29.99,
            business_model=BusinessModel.CHINA_DROPSHIPPING,
            platform="shopify",
        )

        assert result.platform_fee == 0.0
        assert result.platform == "shopify"
        # Only payment processing fee
        assert result.payment_fee > 0

    def test_negative_price_raises(self):
        """Negative prices should raise ValueError."""
        with pytest.raises(ValueError, match="negative"):
            calculate_margin(buy_price=-10, sell_price=20)

        with pytest.raises(ValueError, match="negative"):
            calculate_margin(buy_price=10, sell_price=-5)

    def test_zero_prices(self):
        """Zero prices should work (free product scenario)."""
        result = calculate_margin(buy_price=0, sell_price=0)
        assert result.net_profit <= 0  # Fees still apply

    def test_to_dict(self):
        """Dict output contains all expected keys."""
        result = calculate_margin(buy_price=20, sell_price=40)
        d = result.to_dict()

        expected_keys = {
            "buy_price", "sell_price", "shipping_cost", "packaging_cost",
            "business_model", "platform", "platform_fee", "payment_fee",
            "total_fees", "total_cost", "net_profit", "margin_percent",
            "roi_percent", "markup", "is_profitable",
        }
        assert set(d.keys()) == expected_keys

    def test_summary_output(self):
        """Summary should be a formatted string."""
        result = calculate_margin(buy_price=20, sell_price=50)
        summary = result.summary()

        assert "PROFIT" in summary
        assert "$20.00" in summary
        assert "$50.00" in summary


class TestBatchCalculate:
    """Tests for batch processing."""

    def test_batch_sorted_by_profit(self):
        """Results should be sorted by net_profit descending."""
        products = [
            {"buy_price": 30, "sell_price": 60},   # Low margin
            {"buy_price": 10, "sell_price": 60},    # High margin
            {"buy_price": 20, "sell_price": 60},    # Medium margin
        ]
        results = batch_calculate(products)

        assert len(results) == 3
        assert results[0].net_profit >= results[1].net_profit
        assert results[1].net_profit >= results[2].net_profit

    def test_batch_min_profit_filter(self):
        """Only products meeting min_profit threshold are returned."""
        products = [
            {"buy_price": 45, "sell_price": 50},   # ~Loss
            {"buy_price": 10, "sell_price": 50},    # Good profit
        ]
        results = batch_calculate(products, min_profit=10.0)

        assert len(results) == 1
        assert results[0].buy_price == 10

    def test_batch_empty_list(self):
        """Empty input returns empty output."""
        assert batch_calculate([]) == []
