# DropAgent (Totik)

AI-powered dropshipping assistant for product research, margin analysis, daily digests, Telegram delivery, and a lightweight web dashboard.

## Status

Early development, but the repository already includes:

- Core margin calculator
- eBay comparison and digest generation
- Telegram bot command layer
- Dashboard backend and static frontend
- Multi-user database layer and migrations
- Trend, listing, watchlist, competitor, and export modules

## Repository Structure

```text
.
├── agent/                 # Core business logic and marketplace integrations
├── bot/                   # Telegram bot runtime, handlers, keyboards
├── dashboard/             # Web dashboard backend and frontend
├── db/                    # SQLAlchemy models, sessions, migrations
├── i18n/                  # Translation files and helpers
├── tests/                 # Test suite
├── calc.py                # Margin calculator CLI
├── digest.py              # Daily digest CLI
├── trends.py              # Trends CLI
├── weekly_report.py       # Weekly report CLI
├── docker-compose.yml     # Local stack
├── Dockerfile             # Shared Python image
└── AGENTS.md              # Project operating instructions for AI agents
```

## Quick Start

1. Copy `.env.example` to `.env`
2. Fill in the credentials you want to use
3. Start services:

```bash
docker compose up --build
```

## Main Entry Points

- `python3 calc.py 25 49.99`
- `python3 digest.py --query "airpods pro"`
- `python3 trends.py --category electronics`
- `python3 weekly_report.py --category electronics`
- `python3 -m bot.main`
- `python3 -m dashboard.backend.server`

## GitHub Readiness Notes

The codebase is promising, but it still needs some repository hygiene before it feels polished as a public GitHub project:

- generated/local files should stay out of git
- root documentation should stay stronger than tool-specific instructions
- root CLI files should eventually move into a dedicated `scripts/` or `cli/` package
- internal planning files should be clearly separated from product code

See [docs/STRUCTURE_AUDIT.md](/Users/efsir/Projects/Dropshipping%20agent(Totik)/docs/STRUCTURE_AUDIT.md) for a concrete audit and cleanup plan.
