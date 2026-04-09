# Bot Module

This module contains the Telegram-facing command layer for DropAgent.

Current scope:
- Transport-agnostic command parsing
- `/calc` margin calculator handler
- `/digest` daily digest handler

The code is intentionally framework-light for now so the command behavior can be
tested without depending on a Telegram SDK. A future transport layer can call
the router in `bot/main.py` and send the returned text to Telegram.
