"""Tests for the dashboard HTTP server dispatcher."""

import json

from dashboard.backend.server import dispatch_request


class TestDashboardServer:
    def test_dispatch_serves_frontend_index(self):
        status_code, body, headers = dispatch_request("GET", "/")

        header_map = dict(headers)
        assert status_code == 200
        assert b"DropAgent Dashboard" in body
        assert header_map["Content-Type"].startswith("text/html")

    def test_dispatch_serves_frontend_asset(self):
        status_code, body, headers = dispatch_request("GET", "/app.js")

        header_map = dict(headers)
        assert status_code == 200
        assert b"const API_BASE" in body
        assert "javascript" in header_map["Content-Type"]

    def test_dispatch_routes_api_requests(self):
        status_code, body, headers = dispatch_request(
            "POST",
            "/api/calc",
            body=json.dumps({"buy_price": 25.0, "sell_price": 49.99}).encode("utf-8"),
        )

        payload = json.loads(body.decode("utf-8"))
        assert status_code == 200
        assert payload["buy_price"] == 25.0

    def test_dispatch_unknown_path_returns_not_found(self):
        status_code, body, headers = dispatch_request("GET", "/missing-page")

        payload = json.loads(body.decode("utf-8"))
        assert status_code == 404
        assert payload["error"] == "Not found"
