# Architecture

**Analysis Date:** 2026-04-09

## Pattern Overview

**Overall:** Modular monolith (early stage, only core agent module implemented)

**Key Characteristics:**
- Dataclass-based domain models with self-calculating fields
- Async HTTP client for external API calls
- CLI entry point delegating to pure business logic
- i18n module providing translation across all output
- No web layer, no database, no message queue yet

## Layers

**Agent Layer (Core Business Logic):**
- Purpose: Product analysis, marketplace scanning, margin calculation
- Location: `agent/`
- Contains: Domain models (`MarginResult`, `SoldItem`, `ScanResult`), calculation logic, API clients
- Depends on: `i18n`, `httpx`, standard library
- Used by: CLI (`calc.py`), future bot and dashboard
- Key files:
  - `agent/analyzer.py` - Margin calculator with `calculate_margin()` and `batch_calculate()` functions
  - `agent/scanner.py` - `EbayScanner` class with async `search_sold()` method
  - `agent/__init__.py` - Empty module marker

**i18n Layer (Internationalization):**
- Purpose: Multi-language string translation (en, ru, zh)
- Location: `i18n/`
- Contains: Translation loader, key resolver, language files
- Depends on: Standard library only (`json`, `pathlib`)
- Used by: `agent/analyzer.py` (summary output), `agent/scanner.py` (summary output)
- Key files:
  - `i18n/__init__.py` - `t()` function, `set_language()`, cache management
  - `i18n/en.json`, `i18n/ru.json`, `i18n/zh.json` - Translation dictionaries

**CLI Layer (User Interface):**
- Purpose: Command-line entry point for margin calculator
- Location: `calc.py` (project root)
- Contains: Argument parsing, output formatting
- Depends on: `agent.analyzer`
- Used by: End users directly

**Scaffold Layers (Empty, planned):**
- `bot/` - Telegram bot with `handlers/` and `keyboards/` subdirs
- `dashboard/frontend/` - Web UI (Next.js or plain HTML per CLAUDE.md)
- `dashboard/backend/` - API server
- `db/` - Database models and `migrations/`
- `skills/` - Claude Code skill files

## Data Flow

**Margin Calculation (implemented):**

1. User runs `calc.py` with buy/sell prices and options
2. `argparse` parses CLI args into typed values
3. `calculate_margin()` creates `MarginResult` dataclass
4. `MarginResult.__post_init__()` runs `_calculate()` to compute all fees
5. `result.summary()` calls `t()` for each label, returns formatted string
6. Output printed to stdout

**eBay Scan (implemented, async):**

1. Caller creates `EbayScanner(app_id=...)` or uses env var
2. `search_sold(query, filters...)` builds Finding API params
3. `httpx.AsyncClient` sends GET to eBay Finding API
4. Response JSON parsed by `_parse_finding_response()` into `ScanResult`
5. `ScanResult` aggregates stats (avg/min/max price) via computed properties
6. Rate limiting: HTTP 429 returns empty result instead of raising

**State Management:**
- No persistent state
- i18n cache: module-level `_cache` dict in `i18n/__init__.py`
- Global language: module-level `_current_lang` string in `i18n/__init__.py`
- Scanner HTTP client: instance-level `_client` on `EbayScanner`, lazy-initialized

## Key Abstractions

**MarginResult (`agent/analyzer.py`):**
- Purpose: Complete fee breakdown for a product flip
- Pattern: Dataclass with `__post_init__` auto-calculation
- Outputs: `.summary(lang=)` for display, `.to_dict()` for API, `.is_profitable` property

**ScanResult / SoldItem (`agent/scanner.py`):**
- Purpose: Aggregated eBay sold listing data with individual item details
- Pattern: Dataclass with computed properties (`avg_price`, `min_price`, `max_price`)
- Outputs: `.summary(lang=)` for display, `.to_dict()` for API

**EbayScanner (`agent/scanner.py`):**
- Purpose: Async eBay API client with connection management
- Pattern: Async context manager (`__aenter__`/`__aexit__`), lazy client init
- API: `await scanner.search_sold(query, filters...)`

**Translation function `t()` (`i18n/__init__.py`):**
- Purpose: Resolve dotted key to translated string with variable interpolation
- Pattern: Global function with per-call language override, English fallback
- API: `t("calc.profit", lang="ru", count=42)`

## Entry Points

**CLI (`calc.py`):**
- Location: `calc.py` (project root)
- Triggers: `python calc.py <buy_price> <sell_price> [options]`
- Responsibilities: Parse args, call `calculate_margin()`, print summary

**Scanner (no CLI yet):**
- Location: `agent/scanner.py`
- Triggers: Programmatic only (async), no CLI wrapper
- Responsibilities: Query eBay Finding API, parse response, return structured data

## Error Handling

**Strategy:** Fail fast with ValueError for invalid input, graceful degradation for API errors

**Patterns:**
- Input validation: `ValueError` raised for negative prices (`agent/analyzer.py` line 169)
- API key validation: `ValueError` raised if `EBAY_APP_ID` empty (`agent/scanner.py` line 161)
- Rate limiting: HTTP 429 returns empty `ScanResult` instead of raising (`agent/scanner.py` line 178)
- Malformed API data: Individual items skipped with `continue` in parsing loop (`agent/scanner.py` line 278)
- CLI errors: Caught `ValueError`, printed to stderr, exit code 1 (`calc.py` lines 63-65)

## Cross-Cutting Concerns

**Logging:** Not implemented. No logging framework. Uses `print()` for output and `sys.stderr` for errors.

**Validation:** Manual validation in function bodies. No validation framework (e.g., pydantic).

**Authentication:** Not implemented. API keys read from env vars at runtime.

**Internationalization:** Fully integrated via `i18n.t()`. All user-facing strings go through translation. Three languages supported: en, ru, zh.

---

*Architecture analysis: 2026-04-09*
