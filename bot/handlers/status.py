"""Simple stack status summary for non-technical bot users."""

from __future__ import annotations

from typing import Optional

from agent.capabilities import (
    build_capability_statuses,
    build_next_step,
    capability_label_for_integration,
)
from db.service import UserProfile
from i18n import t


def handle_status_command(
    user_profile: Optional[UserProfile],
    lang: Optional[str] = None,
) -> str:
    """Render a plain-language overview of what is ready now and what can improve later."""
    if user_profile is None:
        return f"{t('common.error', lang=lang)}: {t('common.user_not_available', lang=lang)}"

    lines = [t("status_cmd.title", lang=lang)]
    for capability in build_capability_statuses(user_profile):
        lines.append(
            t(
                "status_cmd.line",
                lang=lang,
                label=capability.label,
                summary=capability.summary,
            )
        )
        if capability.suggested_integrations:
            suggestions = ", ".join(
                capability_label_for_integration(integration_id)
                for integration_id in capability.suggested_integrations
            )
            lines.append(
                t("status_cmd.suggested", lang=lang, suggestions=suggestions)
            )
    lines.extend(
        [
            "",
            t("status_cmd.next_step", lang=lang, action=build_next_step(user_profile, lang=lang)),
        ]
    )
    return "\n".join(lines)
