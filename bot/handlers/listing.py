"""Telegram-style handler for the /listing command."""

from typing import Optional

from agent.listings import bulk_generate_listings
from i18n import t


def handle_listing_command(text: str, lang: Optional[str] = None) -> str:
    """
    Handle `/listing` command text.

    Supports:
        /listing airpods pro
        /listing airpods pro | gaming mouse | lego set
    """
    raw = text[len("/listing"):].strip()
    if not raw:
        return t("listing.usage", lang=lang)

    items = [item.strip() for item in raw.split("|") if item.strip()]
    if not items:
        return f"{t('common.error', lang=lang)}: {t('listing.invalid_input', lang=lang)}"

    drafts = bulk_generate_listings(items)
    if len(drafts) == 1:
        return drafts[0].summary(lang=lang)

    return "\n\n".join(draft.summary(lang=lang) for draft in drafts)
