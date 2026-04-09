# Technology Stack

**Analysis Date:** 2026-04-09

## Languages

**Primary:**
- Python 3.9+ (system Python 3.9.6 detected) - All application code

**Secondary:**
- JSON - Translation files (`i18n/en.json`, `i18n/ru.json`, `i18n/zh.json`)

## Runtime

**Environment:**
- Python 3.9+ (uses `list[dict]` type hint syntax in `agent/analyzer.py` line 197, requires 3.9+)
- macOS development (Darwin 25.3.0)

**Package Manager:**
- pip
- Lockfile: **missing** (no `requirements.lock` or `pip-compile` output)
- Dependencies declared in: `requirements.txt`

## Frameworks

**Core:**
- No web framework yet (planned: Next.js for dashboard frontend, custom API backend)
- No bot framework yet (planned: Telegram Bot)

**Testing:**
- pytest >= 8.0.0 - Test runner (`requirements.txt` line 10)

**Build/Dev:**
- No build tooling configured (no Makefile, no pyproject.toml, no setup.py)
- No Docker configuration yet (planned per CLAUDE.md but not created)

## Key Dependencies

**Critical (from `requirements.txt`):**
- `python-dotenv` >= 1.0.0 - Environment variable loading from `.env` files
- `httpx` >= 0.27.0 - Async HTTP client (used by `agent/scanner.py` for eBay API calls)
- `pytest` >= 8.0.0 - Test framework

**Standard Library (heavily used):**
- `dataclasses` - All data models (`MarginResult`, `SoldItem`, `ScanResult`)
- `enum` - `BusinessModel` enum in `agent/analyzer.py`
- `json` - Translation file loading in `i18n/__init__.py`
- `argparse` - CLI argument parsing in `calc.py`
- `pathlib` - File path handling in `i18n/__init__.py`
- `asyncio` - Async operations in scanner
- `os` - Environment variable access in `agent/scanner.py`

## Configuration

**Environment:**
- `.env.example` defines required variables (never read `.env` contents)
- `python-dotenv` loads `.env` at runtime
- Required env vars for eBay scanning: `EBAY_APP_ID`, `EBAY_CERT_ID`, `EBAY_DEV_ID`
- Planned env vars: `AMAZON_ACCESS_KEY`, `AMAZON_SECRET_KEY`, `AMAZON_PARTNER_TAG`, `WALMART_API_KEY`, `TELEGRAM_BOT_TOKEN`, `DISCORD_WEBHOOK_URL`

**Build:**
- No build configuration files exist
- No `pyproject.toml`, `setup.py`, or `setup.cfg`
- No Docker or docker-compose files yet

## Platform Requirements

**Development:**
- Python 3.9+
- pip for dependency installation
- `pip install -r requirements.txt`

**Production:**
- Planned: Docker Compose single-command deployment (per CLAUDE.md)
- No Dockerfile or docker-compose.yml created yet

## Dependency Count

- 3 direct dependencies total (extremely lean)
- No dev dependency separation (pytest is in main requirements.txt)

---

*Stack analysis: 2026-04-09*
