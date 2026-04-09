# Dashboard Module

This module will hold the DropAgent web dashboard.

Current scope:
- Backend service helpers for calculator and digest data
- JSON-ready payload generation for API endpoints
- Standard-library HTTP API server for dashboard/backend integration

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

The HTTP layer intentionally uses the standard library right now so the project
stays lean while the core product logic stabilizes. A framework like FastAPI can
be added later on top of the same backend service layer.
