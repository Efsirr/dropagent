# Codebase Structure

**Analysis Date:** 2026-04-09

## Directory Layout

```
dropagent/
├── agent/                  # Core AI agent logic (margin calc, scanning)
│   ├── __init__.py
│   ├── analyzer.py         # Margin calculator & product scoring
│   └── scanner.py          # eBay sold listings scanner
├── bot/                    # Telegram bot (scaffolded, empty)
│   ├── handlers/
│   └── keyboards/
├── dashboard/              # Web dashboard (scaffolded, empty)
│   ├── backend/
│   └── frontend/
├── db/                     # Database models (scaffolded, empty)
│   └── migrations/
├── i18n/                   # Internationalization
│   ├── __init__.py         # Translation engine (t(), set_language())
│   ├── en.json             # English translations
│   ├── ru.json             # Russian translations
│   └── zh.json             # Chinese translations
├── skills/                 # Claude Code skills (scaffolded, empty)
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── test_analyzer.py    # 12 tests for margin calculator
│   ├── test_scanner.py     # 13 tests for eBay scanner
│   └── test_i18n.py        # 11 tests for translation system
├── .planning/              # GSD planning documents
│   └── codebase/
├── .env.example            # Environment variable template
├── calc.py                 # CLI entry point for margin calculator
├── CLAUDE.md               # Project instructions for Claude Code
└── requirements.txt        # Python dependencies (3 packages)
```

## Directory Purposes

**`agent/`:**
- Purpose: Core business logic for product research and analysis
- Contains: Python modules with dataclass models, calculation functions, API clients
- Key files: `analyzer.py` (margin math), `scanner.py` (eBay API integration)
- Planned additions per CLAUDE.md: `trends.py`, `listings.py`, `scheduler.py`

**`bot/`:**
- Purpose: Telegram bot for mobile/chat interface
- Contains: Empty scaffold directories only
- Planned: `main.py` entry point, command handlers, inline keyboards

**`dashboard/`:**
- Purpose: Web-based UI for reports and settings
- Contains: Empty scaffold directories only
- Planned: `frontend/` (Next.js or plain HTML), `backend/` (API server)

**`db/`:**
- Purpose: Database models and schema migrations
- Contains: Empty scaffold directories only
- Planned: `models.py`, migration files

**`i18n/`:**
- Purpose: Multi-language support (English, Russian, Chinese)
- Contains: Translation engine and JSON language files
- Key files: `__init__.py` (public API: `t()`, `set_language()`, `get_language()`)

**`tests/`:**
- Purpose: pytest test suite
- Contains: Test modules mirroring `agent/` and `i18n/` structure
- Pattern: One test file per source module, prefixed with `test_`

**`skills/`:**
- Purpose: Claude Code skill definition files
- Contains: Empty (planned: `scanner-skill.md`, `margin-skill.md`, `listing-skill.md`)

## Key File Locations

**Entry Points:**
- `calc.py`: CLI margin calculator (the only runnable entry point currently)

**Configuration:**
- `.env.example`: Template for environment variables
- `requirements.txt`: Python dependencies

**Core Logic:**
- `agent/analyzer.py`: `calculate_margin()`, `batch_calculate()`, `MarginResult`, `BusinessModel`
- `agent/scanner.py`: `EbayScanner`, `SoldItem`, `ScanResult`

**Internationalization:**
- `i18n/__init__.py`: `t(key, lang=, **kwargs)`, `set_language(lang)`, `get_language()`
- `i18n/en.json`: English strings (source of truth for translation keys)

**Testing:**
- `tests/test_analyzer.py`: Margin calculator tests
- `tests/test_scanner.py`: eBay scanner tests (uses mock response data, no live API)
- `tests/test_i18n.py`: Translation system tests

## Naming Conventions

**Files:**
- Snake_case for all Python modules: `analyzer.py`, `scanner.py`, `test_analyzer.py`
- Test files prefixed with `test_`: `test_analyzer.py` mirrors `analyzer.py`
- Language files named by ISO code: `en.json`, `ru.json`, `zh.json`

**Directories:**
- Lowercase, single word: `agent/`, `bot/`, `tests/`, `skills/`
- Compound names use no separator: `i18n/` (abbreviation)

## Where to Add New Code

**New agent module (e.g., trends, listings, scheduler):**
- Implementation: `agent/{module_name}.py`
- Tests: `tests/test_{module_name}.py`
- Translation keys: Add section to all three `i18n/*.json` files
- Follow pattern: dataclass models, public functions, `summary()` method using `t()`

**New Telegram bot handler:**
- Handler: `bot/handlers/{command_name}.py`
- Keyboard layouts: `bot/keyboards/{name}.py`
- Bot entry point: `bot/main.py`

**New API endpoint (dashboard backend):**
- Implementation: `dashboard/backend/`
- No convention established yet

**New database model:**
- Models: `db/models.py`
- Migrations: `db/migrations/`

**New translation keys:**
- Add to ALL three files: `i18n/en.json`, `i18n/ru.json`, `i18n/zh.json`
- Use nested structure: `{"section": {"key": "value"}}`
- Access via dotted path: `t("section.key")`
- Test key parity in `tests/test_i18n.py` `test_all_languages_have_same_keys()`

**New CLI command:**
- Create new file in project root (following `calc.py` pattern)
- Use `argparse` for argument parsing
- Import from `agent/` for business logic

**Utilities / shared helpers:**
- No dedicated utils directory exists yet
- Small shared code lives in relevant module (e.g., i18n cache in `i18n/__init__.py`)
- When needed, create `utils/` at project root

## Special Directories

**`.planning/`:**
- Purpose: GSD planning and analysis documents
- Generated: Yes (by Claude Code agents)
- Committed: Project-specific decision

**`.pytest_cache/`:**
- Purpose: pytest internal cache
- Generated: Yes (by pytest)
- Committed: No (has `.gitignore`)

---

*Structure analysis: 2026-04-09*
