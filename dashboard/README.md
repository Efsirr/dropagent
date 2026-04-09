# Dashboard Module

This module will hold the DropAgent web dashboard.

Current scope:
- Backend service helpers for calculator and digest data
- JSON-ready payload generation for API endpoints
- Standard-library HTTP API server for dashboard/backend integration
- static frontend served directly by the same server

Current API surface:
- `GET /health`
- `POST /api/calc`
- `GET /api/users/<telegram_chat_id>`
- `PATCH /api/users/<telegram_chat_id>/settings`
- `PATCH /api/users/<telegram_chat_id>/schedule`
- `GET /api/users/<telegram_chat_id>/tracked-queries`
- `POST /api/users/<telegram_chat_id>/tracked-queries`
- `DELETE /api/users/<telegram_chat_id>/tracked-queries/<query>`
- `POST /api/users/<telegram_chat_id>/digest-preview`
- `POST /api/digest-preview`
- `POST /api/weekly-report-preview`
- `GET /api/users/<telegram_chat_id>/watchlist`
- `POST /api/users/<telegram_chat_id>/watchlist`
- `DELETE /api/users/<telegram_chat_id>/watchlist/<item_id>`
- `GET /api/users/<telegram_chat_id>/watchlist/<item_id>/history`
- `POST /api/users/<telegram_chat_id>/watchlist/<item_id>/history`
- `GET /api/users/<telegram_chat_id>/competitors`
- `POST /api/users/<telegram_chat_id>/competitors`
- `DELETE /api/users/<telegram_chat_id>/competitors/<competitor_id>`
- `POST /api/users/<telegram_chat_id>/competitors/<competitor_id>/scan`

The HTTP layer intentionally uses the standard library right now so the project
stays lean while the core product logic stabilizes. A framework like FastAPI can
be added later on top of the same backend service layer.

Run modes:
- `python3 -m dashboard.backend.server` starts the API and serves the frontend
- `docker compose up dashboard` starts the same server in a container

Frontend delivery:
- `GET /` serves `dashboard/frontend/index.html`
- static assets like `/app.js` and `/styles.css` are served by the same process
