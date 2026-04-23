"""Catalog of optional DropAgent integrations and baseline requirements."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional

from agent.secrets import mask_secret


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
    credential_fields: tuple["CredentialFieldSpec", ...] = ()


@dataclass(frozen=True)
class CredentialFieldSpec:
    """One user-provided credential field for an integration."""

    key: str
    label: str
    env_var: Optional[str] = None
    required: bool = True
    secret: bool = True
    placeholder: str = ""

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "label": self.label,
            "env_var": self.env_var,
            "required": self.required,
            "secret": self.secret,
            "placeholder": self.placeholder,
        }


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
        credential_fields=(
            CredentialFieldSpec("access_key", "Access Key", env_var="AMAZON_ACCESS_KEY", placeholder="AKIA..."),
            CredentialFieldSpec("secret_key", "Secret Key", env_var="AMAZON_SECRET_KEY"),
            CredentialFieldSpec("partner_tag", "Partner Tag", env_var="AMAZON_PARTNER_TAG", secret=False, placeholder="yourtag-20"),
        ),
    ),
    IntegrationSpec(
        integration_id="walmart",
        label="Walmart Source",
        priority="must_have",
        status="live",
        value="Retail arbitrage source prices and stock checks.",
        env_vars=("WALMART_API_KEY",),
        recommended_for="us_arbitrage",
        credential_fields=(
            CredentialFieldSpec("api_key", "API Key", env_var="WALMART_API_KEY", placeholder="walmart-api-key"),
        ),
    ),
    IntegrationSpec(
        integration_id="aliexpress",
        label="AliExpress Source",
        priority="must_have",
        status="live",
        value="China-model sourcing and catalog search.",
        env_vars=("ALIEXPRESS_APP_KEY", "ALIEXPRESS_APP_SECRET"),
        recommended_for="china_dropshipping",
        credential_fields=(
            CredentialFieldSpec("app_key", "App Key", env_var="ALIEXPRESS_APP_KEY", placeholder="app-key"),
            CredentialFieldSpec("app_secret", "App Secret", env_var="ALIEXPRESS_APP_SECRET"),
            CredentialFieldSpec("tracking_id", "Tracking ID", env_var="ALIEXPRESS_TRACKING_ID", required=False, secret=False, placeholder="optional"),
        ),
    ),
    IntegrationSpec(
        integration_id="cj",
        label="CJDropshipping Source",
        priority="must_have",
        status="live",
        value="China sourcing with supplier and fulfillment coverage.",
        env_vars=("CJ_API_KEY",),
        recommended_for="china_dropshipping",
        credential_fields=(
            CredentialFieldSpec("api_key", "API Key", env_var="CJ_API_KEY", placeholder="cj-api-key"),
        ),
    ),
    IntegrationSpec(
        integration_id="keepa",
        label="Keepa",
        priority="must_have",
        status="live",
        value="Amazon price history and buy-box trend validation.",
        env_vars=("KEEPA_API_KEY",),
        recommended_for="us_arbitrage",
        credential_fields=(
            CredentialFieldSpec("api_key", "API Key", env_var="KEEPA_API_KEY", placeholder="keepa-api-key"),
        ),
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
        status="live",
        value="Shopify competitor discovery and niche tracking.",
        env_vars=("STORELEADS_API_KEY",),
        recommended_for="all",
        credential_fields=(
            CredentialFieldSpec("api_key", "API Key", env_var="STORELEADS_API_KEY", placeholder="storeleads-api-key"),
        ),
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
        status="live",
        value="TikTok ad spy for viral product discovery.",
        env_vars=("PIPIADS_API_KEY",),
        recommended_for="china_dropshipping",
        credential_fields=(
            CredentialFieldSpec("api_key", "API Key", env_var="PIPIADS_API_KEY", placeholder="pipiads-api-key"),
        ),
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


def credential_fields_for_integration(integration_id: str) -> tuple[CredentialFieldSpec, ...]:
    """Return declared credential fields for an integration."""
    spec = get_integration_spec(integration_id)
    return spec.credential_fields if spec else ()


def serialize_integration_credentials(credentials: dict[str, str]) -> str:
    """Serialize normalized credential values for encrypted storage."""
    return json.dumps(credentials, ensure_ascii=False, sort_keys=True)


def deserialize_integration_credentials(
    integration_id: str,
    secret_payload: str,
) -> dict[str, str]:
    """Deserialize saved credential payload into a normalized dict.

    Older single-key records are treated as the first declared field.
    """
    try:
        parsed = json.loads(secret_payload)
    except json.JSONDecodeError:
        parsed = None

    if isinstance(parsed, dict):
        return {
            str(key): str(value).strip()
            for key, value in parsed.items()
            if value is not None and str(value).strip()
        }

    fields = credential_fields_for_integration(integration_id)
    primary_key = fields[0].key if fields else "api_key"
    value = secret_payload.strip()
    return {primary_key: value} if value else {}


def normalize_integration_credentials(
    integration_id: str,
    *,
    api_key: Optional[str] = None,
    credentials: Optional[dict] = None,
) -> dict[str, str]:
    """Validate and normalize user-submitted credential values."""
    spec = get_integration_spec(integration_id)
    if spec is None:
        raise ValueError("unsupported integration")

    field_specs = spec.credential_fields or ()
    if credentials is None:
        if api_key is None:
            if len(field_specs) > 1:
                field_labels = ", ".join(field.label for field in field_specs if field.required)
                raise ValueError(f"{spec.label} requires: {field_labels}")
            raise ValueError("api_key is required")
        if len(field_specs) > 1:
            field_labels = ", ".join(field.label for field in field_specs if field.required)
            raise ValueError(f"{spec.label} requires: {field_labels}")
        key = field_specs[0].key if field_specs else "api_key"
        credentials = {key: api_key}

    if not isinstance(credentials, dict):
        raise ValueError("credentials must be an object")

    normalized: dict[str, str] = {}
    for field in field_specs:
        raw = credentials.get(field.key)
        value = "" if raw is None else str(raw).strip()
        if value:
            normalized[field.key] = value
        elif field.required:
            raise ValueError(f"{field.label} is required")

    if not field_specs:
        value = (api_key or "").strip()
        if not value:
            raise ValueError("api_key is required")
        normalized["api_key"] = value

    if not normalized:
        raise ValueError("credentials are required")
    return normalized


def integration_credentials_from_env(
    integration_id: str,
    env: Optional[dict] = None,
) -> Optional[dict[str, str]]:
    """Return integration credentials from env when fully configured."""
    spec = get_integration_spec(integration_id)
    env = env or {}
    if spec is None:
        return None

    values: dict[str, str] = {}
    for field in spec.credential_fields:
        raw = env.get(field.env_var or "", "").strip() if field.env_var else ""
        if raw:
            values[field.key] = raw
        elif field.required:
            return None
    return values or None


def integration_is_configured(
    integration_id: str,
    *,
    env: Optional[dict] = None,
    connected_integration_ids: Optional[set[str]] = None,
) -> bool:
    """Whether an integration is usable via saved user creds or env fallback."""
    connected_integration_ids = connected_integration_ids or set()
    return (
        integration_id in connected_integration_ids
        or integration_credentials_from_env(integration_id, env) is not None
    )


def integration_secret_hint(
    integration_id: str,
    credentials: dict[str, str],
) -> str:
    """Build a safe hint string for stored credentials."""
    fields = credential_fields_for_integration(integration_id)
    for field in fields:
        value = credentials.get(field.key, "").strip()
        if value:
            return mask_secret(value)
    for value in credentials.values():
        cleaned = value.strip()
        if cleaned:
            return mask_secret(cleaned)
    return ""
