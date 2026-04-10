"""Vercel Function adapter for Telegram webhook updates."""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler

from bot.webhook import handle_telegram_webhook


def _headers_from_handler(request_handler: BaseHTTPRequestHandler) -> dict:
    """Return request headers as a plain dict."""
    return {key: value for key, value in request_handler.headers.items()}


def _read_body(request_handler: BaseHTTPRequestHandler) -> bytes:
    length = int(request_handler.headers.get("Content-Length", "0"))
    if length <= 0:
        return b""
    return request_handler.rfile.read(length)


class handler(BaseHTTPRequestHandler):  # noqa: N801
    """Vercel's Python runtime looks for this handler class."""

    def _send_json(self, status_code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        response = handle_telegram_webhook(
            body=_read_body(self),
            headers=_headers_from_handler(self),
            env=os.environ,
        )
        self._send_json(response.status_code, response.payload)

    def do_GET(self) -> None:  # noqa: N802
        self._send_json(405, {"ok": False, "error": "POST is required"})

