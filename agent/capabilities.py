"""Human-friendly capability summaries derived from setup and integrations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from agent.integrations import get_integration_spec
from db.service import UserProfile
from i18n import t


@dataclass(frozen=True)
class CapabilityStatus:
    """A simple user-facing capability summary."""

    capability_id: str
    label: str
    summary: str
    status: str
    suggested_integrations: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "capability_id": self.capability_id,
            "label": self.label,
            "summary": self.summary,
            "status": self.status,
            "suggested_integrations": list(self.suggested_integrations),
        }


def _has_any(profile: UserProfile, *integration_ids: str) -> bool:
    selected = set(profile.selected_integrations)
    enabled_sources = set(profile.enabled_sources)
    return any(integration_id in selected or integration_id in enabled_sources for integration_id in integration_ids)


def build_capability_statuses(profile: UserProfile) -> list[CapabilityStatus]:
    """Build a simple capability matrix for bot and dashboard UX."""
    statuses: list[CapabilityStatus] = []

    baseline_ready = bool(profile.telegram_chat_id)
    core_sources_ready = bool(profile.enabled_sources)

    if core_sources_ready:
        statuses.append(
            CapabilityStatus(
                capability_id="product_validation",
                label="Product validation",
                summary="You can already compare source prices against eBay demand.",
                status="ready",
                suggested_integrations=("keepa", "zik"),
            )
        )
    else:
        statuses.append(
            CapabilityStatus(
                capability_id="product_validation",
                label="Product validation",
                summary="Choose at least one source to validate products end-to-end.",
                status="needs_setup",
                suggested_integrations=("amazon", "walmart", "aliexpress", "cj"),
            )
        )

    if _has_any(profile, "keepa", "zik"):
        statuses.append(
            CapabilityStatus(
                capability_id="deeper_validation",
                label="Deeper validation",
                summary="Historical price and marketplace intelligence are selected for stronger decisions.",
                status="boosted",
                suggested_integrations=(),
            )
        )
    else:
        statuses.append(
            CapabilityStatus(
                capability_id="deeper_validation",
                label="Deeper validation",
                summary="Add Keepa or ZIK later for price history and deeper demand checks.",
                status="optional",
                suggested_integrations=("keepa", "zik"),
            )
        )

    if baseline_ready:
        statuses.append(
            CapabilityStatus(
                capability_id="trend_discovery",
                label="Trend discovery",
                summary="Google Trends and Reddit signals already help surface movement.",
                status="ready",
                suggested_integrations=("pipiads", "minea"),
            )
        )
    if _has_any(profile, "pipiads", "minea"):
        statuses.append(
            CapabilityStatus(
                capability_id="trend_boost",
                label="Trend boost",
                summary="Ad-spy integrations are selected for stronger product discovery.",
                status="boosted",
                suggested_integrations=(),
            )
        )
    else:
        statuses.append(
            CapabilityStatus(
                capability_id="trend_boost",
                label="Trend boost",
                summary="Add PiPiADS or Minea later to catch product momentum earlier.",
                status="optional",
                suggested_integrations=("pipiads", "minea"),
            )
        )

    if _has_any(profile, "storeleads", "similarweb"):
        statuses.append(
            CapabilityStatus(
                capability_id="competitor_discovery",
                label="Competitor discovery",
                summary="Extra competitor intelligence is selected for store and traffic discovery.",
                status="boosted",
                suggested_integrations=(),
            )
        )
    else:
        statuses.append(
            CapabilityStatus(
                capability_id="competitor_discovery",
                label="Competitor discovery",
                summary="Your eBay competitor tracker works now. Add StoreLeads or SimilarWeb later for broader discovery.",
                status="ready",
                suggested_integrations=("storeleads", "similarweb"),
            )
        )

    if profile.business_model == "china_dropshipping" and _has_any(profile, "aliexpress", "cj"):
        statuses.append(
            CapabilityStatus(
                capability_id="china_sourcing",
                label="China sourcing",
                summary="China-model sourcing is selected and ready to use.",
                status="ready",
                suggested_integrations=(),
            )
        )
    elif profile.business_model == "china_dropshipping":
        statuses.append(
            CapabilityStatus(
                capability_id="china_sourcing",
                label="China sourcing",
                summary="Select AliExpress or CJ to unlock China-model sourcing.",
                status="needs_setup",
                suggested_integrations=("aliexpress", "cj"),
            )
        )

    return statuses


def capability_label_for_integration(integration_id: str) -> str:
    """Return a readable label for a suggested integration."""
    spec = get_integration_spec(integration_id)
    return spec.label if spec else integration_id


def build_next_step(profile: UserProfile, lang: Optional[str] = None) -> str:
    """Return one simple next action for non-technical users."""
    enabled_sources = set(profile.enabled_sources)
    selected = set(profile.selected_integrations)

    if not enabled_sources:
        return t("status_cmd.next_choose_sources", lang=lang)
    if not profile.tracked_queries:
        return t("status_cmd.next_add_query", lang=lang)
    if not profile.digest_enabled:
        return t("status_cmd.next_enable_digest", lang=lang)
    if not ({"keepa", "zik"} & selected):
        return t("status_cmd.next_deeper_validation", lang=lang)
    if not ({"storeleads", "similarweb", "pipiads", "minea"} & selected):
        return t("status_cmd.next_discovery", lang=lang)
    return t("status_cmd.next_ready", lang=lang)
