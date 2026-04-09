# DropAgent — Hosted Mode Task Board

Goal: keep the open-source self-hosted flow, but add an easy hosted flow where a non-technical user finds the public Telegram bot, opens the dashboard, completes setup, and connects their own service keys.

Principle: make it simple. Users should always understand what they get now, what is missing, and the single next action.

---

## Ground Rules

- Do not store user API keys in `.env`.
- `.env` is only for instance-level secrets: public Telegram bot token, app encryption secret, database URL, Supabase service credentials, webhook secret.
- Store user-owned API keys as per-user encrypted integration credentials.
- Never return raw API keys from API responses after saving them.
- Keep self-hosted Docker/polling mode working while adding hosted/webhook mode.
- All new setup UI must use plain-language labels: "Connect Keepa for Amazon price history", not "configure KEEPA_API_KEY".
- Run `python3 -m pytest tests/ -q` before handing off.

---

## Suggested Parallel Split

### Codex Track

Backend/security/Telegram transport.

### Claude Track

Dashboard setup UX + docs. Stay mostly in `dashboard/frontend/` and documentation unless a small API contract change is already agreed.

---

## Phase 1 — Hosted Foundation

- [x] **1A — Per-user integration secrets model** [Codex]
  - Add DB table for per-user integration credentials.
  - Fields: `id`, `user_id`, `integration_id`, `encrypted_secret`, `secret_hint`, `status`, `last_checked_at`, timestamps.
  - Add migration.
  - Add DB service helpers: save, list status, delete, mark checked.
  - Tests: `tests/test_user_integrations.py`.

- [x] **1B — App encryption service** [Codex]
  - Add small encryption/decryption module for user-owned API keys.
  - Use an app-level secret from env.
  - Store only encrypted values and safe hints.
  - Support key masking: `sk_live_...abcd` -> `sk_...abcd` or similar.
  - Tests: secret round-trip, wrong secret fails, payload/API never exposes raw key.

- [x] **1C — Integration connection API** [Codex]
  - Add dashboard backend endpoints for integration credentials.
  - Proposed endpoints:
    - `GET /api/users/<telegram_chat_id>/integrations`
    - `PUT /api/users/<telegram_chat_id>/integrations/<integration_id>/secret`
    - `DELETE /api/users/<telegram_chat_id>/integrations/<integration_id>/secret`
  - Return only status, label, configured, selected, hint, next action.
  - Tests: `tests/test_dashboard_api.py`.

- [ ] **1D — Telegram webhook mode** [Codex]
  - Keep existing polling mode.
  - Add webhook request handler that accepts Telegram update JSON and calls existing `process_update`.
  - Verify Telegram webhook secret header when configured.
  - Add small server/API entrypoint usable on hosted platforms.
  - Tests: valid webhook update, bad secret rejected, non-message update handled.

- [ ] **1E — Dashboard deep-link from Telegram** [Codex]
  - Add config: `DASHBOARD_PUBLIC_URL`.
  - `/start` and `/setup` should include a simple "Open dashboard" button when public URL exists.
  - Dashboard URL should include enough safe context to load/create the profile.
  - Do not include API keys or privileged tokens in the URL.
  - Tests: bot response includes button when configured and omits it when not configured.

---

## Phase 2 — User Setup UX

- [~] **2A — Dashboard connect-services panel** [Claude — in progress]
  - In setup, show service cards with plain-language value:
    - Keepa: Amazon price history
    - ZIK: deeper eBay validation
    - StoreLeads: discover competitor stores
    - PiPiADS/Minea: ad/trend discovery
  - Each card has one simple action: `Connect`, `Connected`, or `Add later`.
  - Never show env-var names as the main label. Env names can live in advanced/help text.
  - Stay in `dashboard/frontend/` unless an API endpoint from Phase 1 is ready.

- [ ] **2B — Dashboard secret entry flow** [Claude/Codex coordinate]
  - Web form to paste one service key at a time.
  - Immediately clear input after save.
  - Show masked hint only.
  - Show simple success copy: "Keepa connected. Amazon history can be added to product checks."
  - Add accessible error text for failed save.

- [ ] **2C — Telegram `/connect` guided flow** [Codex]
  - `/connect` lists supported services in simple language.
  - `/connect keepa` explains where key is used and asks user to send it.
  - Save the next message as that integration secret, then delete/avoid echoing the key where possible.
  - Add `/disconnect <service>`.
  - Tests for connect state machine.

- [ ] **2D — Plain-language setup copy pass** [Claude]
  - Review Telegram and dashboard setup copy.
  - Replace developer terms where possible:
    - "env" -> "server setting" or hide it
    - "integration" -> "service" when speaking to the user
    - "credentials" -> "API key"
  - Keep docs technical where needed; keep bot/dashboard friendly.

---

## Phase 3 — Hosted Deployment Path

- [ ] **3A — Supabase-ready database notes** [Codex/Claude]
  - Add a short hosted-mode guide.
  - Explain Supabase Postgres URL, migrations, and user-data responsibility.
  - Mention RLS/auth as a hosted-dashboard hardening step before public launch.

- [ ] **3B — Vercel-compatible API plan** [Codex]
  - Decide if dashboard backend stays Python WSGI-ish, becomes FastAPI, or gets thin serverless wrappers.
  - Document the chosen route before a large refactor.
  - Keep Docker mode working.

- [ ] **3C — Public bot launch checklist** [Claude]
  - Add a short checklist:
    - rotate token
    - set webhook
    - set public dashboard URL
    - set encryption secret
    - set database URL
    - test `/start`
    - test dashboard setup
  - Write for non-experts.

---

## Later — Use Connected User Keys

- [ ] **4A — Keepa adapter**
  - Use the current user's saved Keepa key.
  - Add Amazon price history enrichment to product validation/watchlist.

- [ ] **4B — StoreLeads adapter**
  - Use the current user's saved StoreLeads key.
  - Add competitor/store discovery suggestions.

- [ ] **4C — PiPiADS or Minea adapter**
  - Use the current user's saved ad-spy key.
  - Add paid trend signal as a boost, not a requirement.

---

## Definition of Done for Hosted MVP

- A new user can find the public Telegram bot and send `/start`.
- Bot gives a dashboard button and one clear next step.
- User can connect/disconnect at least one optional service key from dashboard.
- Saved user keys are encrypted at rest.
- API responses show only status + masked hint.
- Existing self-hosted `.env` setup still works.
- Tests pass.
