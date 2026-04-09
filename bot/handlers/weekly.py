"""Telegram-style handler for the /weekly command."""

from __future__ import annotations

import argparse
import shlex
from typing import Callable, Optional

from i18n import t
from weekly_report import parse_args, run_weekly_report


def _parse_weekly_text(text: str) -> argparse.Namespace:
    parts = shlex.split(text.strip())
    cli_args = parts[1:] if parts else []

    if cli_args and not any(arg.startswith("--") for arg in cli_args):
        categories = []
        for category in cli_args:
            categories.extend(["--category", category])
        cli_args = categories

    return parse_args(cli_args)


async def handle_weekly_command(
    text: str,
    env: Optional[dict] = None,
    lang: Optional[str] = None,
    runner: Optional[Callable] = None,
) -> str:
    """Handle `/weekly` category report requests."""
    runner = runner or run_weekly_report
    try:
        args = _parse_weekly_text(text)
        return await runner(args, env)
    except ValueError as error:
        return f"{t('common.error', lang=lang)}: {error}"
