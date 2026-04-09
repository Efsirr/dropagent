"""First-run onboarding helpers for Telegram bot setup guidance."""

from __future__ import annotations

from typing import Optional

from agent.integrations import (
    BASELINE_REQUIREMENTS,
    env_vars_configured,
    get_recommended_integrations,
)
from db.service import UserProfile
from i18n import t


def _status_label(is_ready: bool, lang: Optional[str] = None) -> str:
    return t("onboarding.ready", lang=lang) if is_ready else t("onboarding.missing", lang=lang)


def render_baseline_status(env: Optional[dict] = None, lang: Optional[str] = None) -> str:
    """Render baseline env health for this DropAgent instance."""
    lines = [t("onboarding.baseline_title", lang=lang)]
    for requirement in BASELINE_REQUIREMENTS:
        configured = env_vars_configured(env, (requirement.env_var,))
        lines.append(
            t(
                "onboarding.baseline_line",
                lang=lang,
                label=requirement.label,
                status=_status_label(configured, lang=lang),
                env_var=requirement.env_var,
            )
        )
    return "\n".join(lines)


def render_onboarding_welcome(
    env: Optional[dict] = None,
    lang: Optional[str] = None,
) -> str:
    """Intro text for first-run setup."""
    return (
        f"{t('onboarding.title', lang=lang)}\n"
        f"{t('onboarding.intro', lang=lang)}\n\n"
        f"{render_baseline_status(env=env, lang=lang)}\n\n"
        f"{t('onboarding.cta', lang=lang)}"
    )


def render_model_prompt(lang: Optional[str] = None) -> str:
    """Ask the user to choose a primary workflow."""
    return (
        f"{t('onboarding.model_title', lang=lang)}\n"
        f"{t('onboarding.model_intro', lang=lang)}"
    )


def render_integration_recommendations(
    user_profile: UserProfile,
    env: Optional[dict] = None,
    lang: Optional[str] = None,
) -> str:
    """Show recommended connectors for the chosen business model."""
    selected = set(user_profile.selected_integrations)
    lines = [
        t(
            "onboarding.integrations_title",
            lang=lang,
            model=t(f"onboarding.model_{user_profile.business_model}", lang=lang),
        ),
        render_baseline_status(env=env, lang=lang),
        "",
        t("onboarding.integrations_intro", lang=lang),
    ]

    for spec in get_recommended_integrations(user_profile.business_model):
        configured = env_vars_configured(env, spec.env_vars)
        selected_marker = "x" if spec.integration_id in selected else " "
        lines.append(
            t(
                "onboarding.integration_line",
                lang=lang,
                selected=selected_marker,
                label=spec.label,
                priority=spec.priority.replace("_", " "),
                status=t(f"onboarding.status_{spec.status}", lang=lang),
                ready=_status_label(configured, lang=lang),
                value=spec.value,
            )
        )

    lines.extend(
        [
            "",
            t("onboarding.starter_pack_title", lang=lang),
            t("onboarding.starter_pack_body", lang=lang),
        ]
    )
    return "\n".join(lines)


def render_onboarding_complete(
    user_profile: UserProfile,
    lang: Optional[str] = None,
) -> str:
    """Summarize the saved setup after onboarding is done."""
    sources = ", ".join(user_profile.enabled_sources) or t("common.none", lang=lang)
    integrations = ", ".join(user_profile.selected_integrations) or t("common.none", lang=lang)
    return (
        f"{t('onboarding.complete_title', lang=lang)}\n"
        f"{t('onboarding.complete_model', lang=lang)}: "
        f"{t(f'onboarding.model_{user_profile.business_model}', lang=lang)}\n"
        f"{t('onboarding.complete_sources', lang=lang)}: {sources}\n"
        f"{t('onboarding.complete_integrations', lang=lang)}: {integrations}\n"
        f"{t('onboarding.complete_next', lang=lang)}"
    )
