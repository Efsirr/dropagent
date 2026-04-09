"""Tiny standard-library HTTP server for the dashboard backend API."""

from __future__ import annotations

import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from dashboard.backend.api import handle_api_request

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
DEFAULT_INDEX = FRONTEND_DIR / "index.html"


class DashboardAPIHandler(BaseHTTPRequestHandler):
    """HTTP request handler that delegates to the dashboard API router."""

    env: dict = os.environ

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return b""
        return self.rfile.read(length)

    def _send_response(
        self,
        status_code: int,
        body: bytes,
        headers: list[tuple[str, str]],
    ) -> None:
        self.send_response(status_code)
        for key, value in headers:
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _send(self, method: str) -> None:
        status_code, body, headers = dispatch_request(
            method=method,
            path=self.path,
            body=self._read_body(),
            env=self.env,
        )
        self._send_response(status_code, body, headers)

    def do_GET(self) -> None:  # noqa: N802
        self._send("GET")

    def do_POST(self) -> None:  # noqa: N802
        self._send("POST")

    def do_PATCH(self) -> None:  # noqa: N802
        self._send("PATCH")

    def do_DELETE(self) -> None:  # noqa: N802
        self._send("DELETE")

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        """Silence default stdout request logging."""
        del format, args


def run_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    env: Optional[dict] = None,
) -> None:
    """Run the dashboard API HTTP server."""
    DashboardAPIHandler.env = env or os.environ
    server = ThreadingHTTPServer((host, port), DashboardAPIHandler)
    try:
        server.serve_forever()
    finally:
        server.server_close()


def main() -> int:
    """CLI entry point for the dashboard backend API server."""
    load_dotenv()
    host = os.getenv("DASHBOARD_HOST", "127.0.0.1")
    port = int(os.getenv("DASHBOARD_PORT", "8000"))
    run_server(host=host, port=port, env=os.environ)
    return 0


def _file_response(file_path: Path) -> tuple[int, bytes, list[tuple[str, str]]]:
    body = file_path.read_bytes()
    content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
    headers = [
        ("Content-Type", f"{content_type}; charset=utf-8" if content_type.startswith("text/") or content_type == "application/javascript" else content_type),
        ("Content-Length", str(len(body))),
    ]
    return 200, body, headers


def _resolve_frontend_path(path: str) -> Optional[Path]:
    normalized = path.split("?", 1)[0]
    if normalized in ("", "/"):
        return DEFAULT_INDEX

    relative = normalized.lstrip("/")
    candidate = (FRONTEND_DIR / relative).resolve()
    try:
        candidate.relative_to(FRONTEND_DIR.resolve())
    except ValueError:
        return None

    if candidate.is_file():
        return candidate
    return None


def dispatch_request(
    method: str,
    path: str,
    body: bytes = b"",
    env: Optional[dict] = None,
) -> tuple[int, bytes, list[tuple[str, str]]]:
    """Dispatch an incoming HTTP request to either the API or static frontend."""
    if path.startswith("/api/") or path == "/health":
        response = handle_api_request(
            method=method,
            path=path,
            body=body,
            env=env,
        )
        return response.to_http()

    if method == "GET":
        frontend_file = _resolve_frontend_path(path)
        if frontend_file is not None:
            return _file_response(frontend_file)

    response = handle_api_request(method=method, path=path, body=body, env=env)
    return response.to_http()


if __name__ == "__main__":
    raise SystemExit(main())
