"""Telegram-style handler for the /digest command."""

import argparse
import shlex
from typing import Callable, Optional

from db.service import UserProfile
from digest import parse_args, run_digest
from i18n import t


def _parse_digest_text(text: str) -> argparse.Namespace:
    parts = shlex.split(text.strip())
    cli_args = parts[1:] if parts else []

    if cli_args and not any(arg.startswith("--") for arg in cli_args):
        queries = []
        for query in cli_args:
            queries.extend(["--query", query])
        cli_args = queries

    return parse_args(cli_args)


async def handle_digest_command(
    text: str,
    env: Optional[dict] = None,
    lang: Optional[str] = None,
    runner: Optional[Callable] = None,
    user_profile: Optional[UserProfile] = None,
) -> str:
    """
    Handle `/digest` command text.

    Supports either explicit CLI-style flags or shorthand queries:
        /digest airpods mouse
        /digest --query "airpods pro" --top 5
    """
    runner = runner or run_digest

    try:
        args = _parse_digest_text(text)
        if not args.query and user_profile is not None:
            args.query = [item.query for item in user_profile.tracked_queries]
        if user_profile is not None:
            if args.min_profit == 5.0:
                args.min_profit = user_profile.min_profit_threshold
            if args.max_buy_price is None:
                args.max_buy_price = user_profile.max_buy_price
            if not args.source and user_profile.enabled_sources:
                args.source = user_profile.enabled_sources
            args.telegram_chat_id = user_profile.telegram_chat_id
        return await runner(args, env)
    except ValueError as error:
        return f"{t('common.error', lang=lang)}: {error}"
