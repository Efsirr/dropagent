# Bot Module

This module contains the Telegram-facing command layer for DropAgent.

Current scope:
- Transport-agnostic command parsing
- `/calc` margin calculator handler
- `/digest` daily digest handler
- persistent user settings and tracked queries
- scheduled auto-digest delivery via polling loop

The code is intentionally framework-light for now so the command behavior can be
tested without depending on a Telegram SDK.

Current runtime:
- `python3 -m bot.main` starts Telegram long polling
- scheduled digests are checked inside the polling loop
- Docker health checks use a heartbeat file refreshed by the bot process

Main commands:
- `/calc`
- `/digest`
- `/weekly`
- `/listing`
- `/competitor`, `/competitors`, `/uncompetitor`, `/checkcompetitor`
- `/track`, `/tracklist`, `/untrack`
- `/watch`, `/watchlist`, `/unwatch`, `/pricepoint`
- `/settings`, `/language`, `/minprofit`, `/maxbuy`, `/sources`
- `/schedule`
