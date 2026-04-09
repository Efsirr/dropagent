"""Catalog of optional DropAgent integrations and baseline requirements."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class BaselineRequirement:
    """Minimal env requirement to run the instance at all."""

    env_var: str
    label: str
    purpose: str


@dataclass(frozen=True)
class IntegrationSpec:
    """Metadata for a connector or external intelligence service."""

    integration_id: str
    label: str
    priority: str
    status: str
    value: str
    env_vars: tuple[str, ...] = ()
    recommended_for: str = "all"


BASELINE_REQUIREMENTS: tuple[BaselineRequirement, ...] = (
    BaselineRequirement(
        env_var="TELEGRAM_BOT_TOKEN",
        label="Telegram Bot",
        purpose="Lets users interact with DropAgent in Telegram.",
    ),
    BaselineRequirement(
        env_var="EBAY_APP_ID",
        label="eBay Sold Data",
        purpose="Required for demand validation and price comparison.",
    ),
    BaselineRequirement(
        env_var="DATABASE_URL",
        label="Database",
        purpose="Stores users, settings, watchlists, and reports.",
    ),
)


INTEGRATION_SPECS: tuple[IntegrationSpec, ...] = (
    IntegrationSpec(
        integration_id="amazon",
        label="Amazon Source",
        priority="must_have",
        status="live",
        value="Retail arbitrage source prices and product matching.",
        env_vars=("AMAZON_ACCESS_KEY", "AMAZON_SECRET_KEY", "AMAZON_PARTNER_TAG"),
        recommended_for="us_arbitrage",
    ),
    IntegrationSpec(
        integration_id="walmart",
        label="Walmart Source",
        priority="must_have",
        status="live",
        value="Retail arbitrage source prices and stock checks.",
        env_vars=("WALMART_API_KEY",),
        recommended_for="us_arbitrage",
    ),
    IntegrationSpec(
        integration_id="aliexpress",
        label="AliExpress Source",
        priority="must_have",
        status="live",
        value="China-model sourcing and catalog search.",
        env_vars=("ALIEXPRESS_APP_KEY", "ALIEXPRESS_APP_SECRET"),
        recommended_for="china_dropshipping",
    ),
    IntegrationSpec(
        integration_id="cj",
        label="CJDropshipping Source",
        priority="must_have",
        status="live",
        value="China sourcing with supplier and fulfillment coverage.",
        env_vars=("CJ_API_KEY",),
        recommended_for="china_dropshipping",
    ),
    IntegrationSpec(
        integration_id="keepa",
        label="Keepa",
        priority="must_have",
        status="planned",
        value="Amazon price history and buy-box trend validation.",
        env_vars=("KEEPA_API_KEY",),
        recommended_for="us_arbitrage",
    ),
    IntegrationSpec(
        integration_id="zik",
        label="ZIK Analytics",
        priority="must_have",
        status="planned",
        value="Deeper eBay demand and competitor intelligence.",
        env_vars=("ZIK_API_KEY",),
        recommended_for="us_arbitrage",
    ),
    IntegrationSpec(
        integration_id="storeleads",
        label="StoreLeads",
        priority="high_value",
        status="planned",
        value="Shopify competitor discovery and niche tracking.",
        env_vars=("STORELEADS_API_KEY",),
        recommended_for="all",
    ),
    IntegrationSpec(
        integration_id="similarweb",
        label="SimilarWeb",
        priority="high_value",
        status="planned",
        value="Traffic intelligence for competitor validation.",
        env_vars=("SIMILARWEB_API_KEY",),
        recommended_for="all",
    ),
    IntegrationSpec(
        integration_id="pipiads",
        label="PiPiADS",
        priority="high_value",
        status="planned",
        value="TikTok ad spy for viral product discovery.",
        env_vars=("PIPIADS_API_KEY",),
        recommended_for="china_dropshipping",
    ),
    IntegrationSpec(
        integration_id="minea",
        label="Minea",
        priority="high_value",
        status="planned",
        value="Cross-platform ad spy for trend discovery.",
        env_vars=("MINEA_API_KEY",),
        recommended_for="all",
    ),
)


def get_integration_spec(integration_id: str) -> Optional[IntegrationSpec]:
    """Return a single integration definition by id."""
    return next(
        (spec for spec in INTEGRATION_SPECS if spec.integration_id == integration_id),
        None,
    )


def get_recommended_integrations(business_model: str) -> list[IntegrationSpec]:
    """Return integrations relevant for a user's primary model."""
    if business_model not in {"us_arbitrage", "china_dropshipping"}:
        business_model = "us_arbitrage"

    recommended: list[IntegrationSpec] = []
    for spec in INTEGRATION_SPECS:
        if spec.recommended_for in {"all", business_model}:
            recommended.append(spec)
    return recommended


def env_vars_configured(env: Optional[dict], env_vars: tuple[str, ...]) -> bool:
    """Check whether a connector's env variables are all present."""
    env = env or {}
    if not env_vars:
        return True
    return all(bool(env.get(env_var, "").strip()) for env_var in env_vars)
