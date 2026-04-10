# DropAgent — Vercel Adapter Plan

This plan keeps the current Python core and Docker/self-hosted mode. Do not convert the project to Next.js or FastAPI just to deploy a preview.

---

## Current Backend Shape

DropAgent already has framework-agnostic routers:

- Dashboard/static dispatcher: `dashboard.backend.server.dispatch_request(...)`
- Dashboard JSON API router: `dashboard.backend.api.handle_api_request(...)`
- Telegram webhook handler: `bot.webhook.handle_telegram_webhook(...)`

Those should remain the source of truth.

---

## Implemented Vercel Shape

DropAgent uses tiny Python Vercel Functions under `/api`.

Vercel's Python runtime can expose a function from a file in `/api` with:

```python
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    ...
```

Use that style for thin adapters only.

---

## Files

```text
api/index.py
api/telegram/webhook.py
vercel.json
```

Status: these thin adapters now exist. Keep them thin; route future behavior through the framework-agnostic Python modules listed above.

### `api/index.py`

Purpose:

- Serve dashboard static assets.
- Serve existing `/api/...` JSON routes.
- Delegate to `dashboard.backend.server.dispatch_request`.

No business logic should live here.

### `api/telegram/webhook.py`

Purpose:

- Receive Telegram POST updates.
- Pass body + headers + env to `bot.webhook.handle_telegram_webhook`.
- Return JSON status.

No command routing should live here.

### `vercel.json`

Purpose:

- Route dashboard requests to `api/index.py`.
- Route Telegram webhook requests to `api/telegram/webhook.py`.
- Optionally set Python function duration.

Implemented route shape:

```json
{
  "rewrites": [
    {
      "source": "/telegram/webhook",
      "destination": "/api/telegram/webhook"
    },
    {
      "source": "/api/:path*",
      "destination": "/api/index?dropagent_path=/api/:path*"
    },
    {
      "source": "/:path*",
      "destination": "/api/index?dropagent_path=/:path*"
    }
  ]
}
```

The `dropagent_path` query value is adapter plumbing. It preserves the original visitor-facing path after Vercel rewrites the request into `api/index.py`.

---

## Environment Variables on Vercel

Minimum hosted preview:

```env
DATABASE_URL=
APP_SECRET_KEY=
TELEGRAM_BOT_TOKEN=
TELEGRAM_WEBHOOK_SECRET=
DASHBOARD_PUBLIC_URL=
EBAY_APP_ID=
```

Optional instance-level keys still work for self-hosted/demo mode, but public hosted users should connect their own keys through the setup flow.

---

## What Not To Do Yet

- Do not run the long-polling bot process on Vercel.
- Do not add user-owned API keys to Vercel env vars.
- Do not expose Supabase service-role credentials to browser JavaScript.
- Do not rewrite the existing dashboard backend until the thin adapter has been tested.

---

## First Preview Definition

First Vercel preview is ready when:

- `/` serves dashboard HTML.
- `/api/calc` returns JSON.
- `/api/users/<telegram_chat_id>` returns JSON.
- `/telegram/webhook` accepts a Telegram update JSON POST.
- Bad webhook secret returns unauthorized.
- The same code still passes `python3 -m pytest tests/ -q`.
