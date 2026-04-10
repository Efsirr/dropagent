"""Vercel Function adapter for the DropAgent dashboard and JSON API."""

from __future__ import annotations

import os
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qsl, urlencode, urlparse

from dashboard.backend.server import dispatch_request


DROPAGENT_PATH_PARAM = "dropagent_path"


def _headers_from_handler(request_handler: BaseHTTPRequestHandler) -> dict:
    """Return request headers as a plain dict."""
    return {key: value for key, value in request_handler.headers.items()}


def _read_body(request_handler: BaseHTTPRequestHandler) -> bytes:
    length = int(request_handler.headers.get("Content-Length", "0"))
    if length <= 0:
        return b""
    return request_handler.rfile.read(length)


def _original_path(vercel_path: str) -> str:
    """Recover the pre-rewrite path routed into this Vercel Function."""
    parsed = urlparse(vercel_path)
    query_items = parse_qsl(parsed.query, keep_blank_values=True)
    recovered_path = None
    forwarded_query_items = []

    for key, value in query_items:
        if key == DROPAGENT_PATH_PARAM and recovered_path is None:
            recovered_path = value or "/"
        else:
            forwarded_query_items.append((key, value))

    path = recovered_path or parsed.path or "/"
    forwarded_query = urlencode(forwarded_query_items, doseq=True)
    if forwarded_query:
        return f"{path}?{forwarded_query}"
    return path


class handler(BaseHTTPRequestHandler):  # noqa: N801
    """Vercel's Python runtime looks for this handler class."""

    def _send(self, method: str) -> None:
        status_code, body, headers = dispatch_request(
            method=method,
            path=_original_path(self.path),
            body=_read_body(self),
            env=os.environ,
        )

        self.send_response(status_code)
        for key, value in headers:
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        self._send("GET")

    def do_POST(self) -> None:  # noqa: N802
        self._send("POST")

    def do_PATCH(self) -> None:  # noqa: N802
        self._send("PATCH")

    def do_DELETE(self) -> None:  # noqa: N802
        self._send("DELETE")

