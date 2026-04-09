"""Telegram-style handlers for the product watchlist."""

from __future__ import annotations

from typing import Optional

from db.service import (
    SUPPORTED_SOURCES,
    UserProfile,
    add_watchlist_item,
    add_watchlist_price_point,
    list_watchlist_items,
    remove_watchlist_item,
)
from db.session import get_database_url, get_session
from i18n import t


def _get_chat_id(user_profile: Optional[UserProfile]) -> Optional[str]:
    if user_profile is None:
        return None
    return user_profile.telegram_chat_id


def handle_watch_command(
    text: str,
    env: Optional[dict] = None,
    user_profile: Optional[UserProfile] = None,
    lang: Optional[str] = None,
) -> str:
    """Add a product to the current user's watchlist."""
    chat_id = _get_chat_id(user_profile)
    if chat_id is None:
        return f"{t('common.error', lang=lang)}: {t('common.user_not_available', lang=lang)}"

    raw = text[len("/watch"):].strip()
    parts = [part.strip() for part in raw.split("|")]
    if len(parts) < 2:
        return t("watch.usage", lang=lang)

    source = parts[0].lower()
    if source not in SUPPORTED_SOURCES:
        return f"{t('common.error', lang=lang)}: {t('watch.unsupported_source', lang=lang)}"

    product_name = parts[1]
    current_buy_price = None
    product_url = None

    if len(parts) >= 3 and parts[2]:
        try:
            current_buy_price = float(parts[2])
        except ValueError:
            product_url = parts[2]

    if len(parts) >= 4:
        product_url = parts[3] or product_url

    session = get_session(get_database_url(env))
    try:
        item = add_watchlist_item(
            session,
            telegram_chat_id=chat_id,
            source=source,
            product_name=product_name,
            current_buy_price=current_buy_price,
            product_url=product_url,
        )
        result = t("watch.saved", lang=lang, item_id=item.item_id, name=item.product_name, source=item.source)
        if item.current_buy_price is not None:
            result += f"\n{t('watch.current_buy', lang=lang, price=f'{item.current_buy_price:.2f}')}"
        return result
    finally:
        session.close()


def handle_watchlist_command(
    env: Optional[dict] = None,
    user_profile: Optional[UserProfile] = None,
    lang: Optional[str] = None,
) -> str:
    """Render the current user's watchlist."""
    chat_id = _get_chat_id(user_profile)
    if chat_id is None:
        return f"{t('common.error', lang=lang)}: {t('common.user_not_available', lang=lang)}"

    session = get_session(get_database_url(env))
    try:
        items = list_watchlist_items(session, telegram_chat_id=chat_id)
    finally:
        session.close()

    if not items:
        return t("watchlist.empty", lang=lang)

    lines = [t("watchlist.title", lang=lang)]
    for item in items:
        bits = [item.source]
        if item.current_buy_price is not None:
            bits.append(f"{t('watchlist.buy', lang=lang)} ${item.current_buy_price:.2f}")
        if item.current_sell_price is not None:
            bits.append(f"{t('watchlist.sell', lang=lang)} ${item.current_sell_price:.2f}")
        if item.price_history:
            bits.append(t("watchlist.points", lang=lang, count=len(item.price_history)))
        lines.append(f'#{item.item_id} "{item.product_name}" ({", ".join(bits)})')
    return "\n".join(lines)


def handle_unwatch_command(
    text: str,
    env: Optional[dict] = None,
    user_profile: Optional[UserProfile] = None,
    lang: Optional[str] = None,
) -> str:
    """Remove a product from the current user's watchlist."""
    chat_id = _get_chat_id(user_profile)
    if chat_id is None:
        return f"{t('common.error', lang=lang)}: {t('common.user_not_available', lang=lang)}"

    parts = text.strip().split()
    if len(parts) != 2:
        return t("unwatch.usage", lang=lang)

    try:
        item_id = int(parts[1])
    except ValueError:
        return f"{t('common.error', lang=lang)}: {t('unwatch.invalid_id', lang=lang)}"

    session = get_session(get_database_url(env))
    try:
        items = remove_watchlist_item(session, telegram_chat_id=chat_id, item_id=item_id)
        return t("unwatch.removed", lang=lang, item_id=item_id, remaining=len(items))
    except ValueError as error:
        return f"{t('common.error', lang=lang)}: {error}"
    finally:
        session.close()


def handle_pricepoint_command(
    text: str,
    env: Optional[dict] = None,
    user_profile: Optional[UserProfile] = None,
    lang: Optional[str] = None,
) -> str:
    """Add a new price point to an existing watchlist item."""
    chat_id = _get_chat_id(user_profile)
    if chat_id is None:
        return f"{t('common.error', lang=lang)}: {t('common.user_not_available', lang=lang)}"

    parts = text.strip().split()
    if len(parts) not in (3, 4):
        return t("pricepoint.usage", lang=lang)

    try:
        item_id = int(parts[1])
        buy_price = float(parts[2])
        sell_price = float(parts[3]) if len(parts) == 4 else None
    except ValueError:
        return f"{t('common.error', lang=lang)}: {t('pricepoint.invalid_numbers', lang=lang)}"

    session = get_session(get_database_url(env))
    try:
        item = add_watchlist_price_point(
            session,
            telegram_chat_id=chat_id,
            item_id=item_id,
            buy_price=buy_price,
            sell_price=sell_price,
        )
        sell_suffix = (
            t("pricepoint.sell_suffix", lang=lang, sell_price=f"{item.current_sell_price:.2f}")
            if item.current_sell_price is not None
            else ""
        )
        return t(
            "pricepoint.saved",
            lang=lang,
            item_id=item.item_id,
            name=item.product_name,
            buy_price=f"{item.current_buy_price:.2f}",
            sell_suffix=sell_suffix,
            history_count=len(item.price_history),
        )
    except ValueError as error:
        return f"{t('common.error', lang=lang)}: {error}"
    finally:
        session.close()
