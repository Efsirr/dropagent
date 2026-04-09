"""Framework-agnostic JSON API router for the dashboard backend."""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import parse_qs, unquote, urlparse

from dashboard.backend.service import (
    add_tracked_query_payload,
    calculate_margin_payload,
    generate_digest_payload,
    generate_saved_digest_payload,
    get_user_profile_payload,
    list_tracked_queries_payload,
    remove_tracked_query_payload,
    update_digest_schedule_payload,
    update_user_settings_payload,
)


USER_BASE_RE = re.compile(r"^/api/users/(?P<chat_id>[^/]+)$")
USER_SETTINGS_RE = re.compile(r"^/api/users/(?P<chat_id>[^/]+)/settings$")
USER_SCHEDULE_RE = re.compile(r"^/api/users/(?P<chat_id>[^/]+)/schedule$")
USER_TRACKED_QUERIES_RE = re.compile(r"^/api/users/(?P<chat_id>[^/]+)/tracked-queries$")
USER_TRACKED_QUERY_ITEM_RE = re.compile(
    r"^/api/users/(?P<chat_id>[^/]+)/tracked-queries/(?P<query>.+)$"
)
USER_DIGEST_PREVIEW_RE = re.compile(r"^/api/users/(?P<chat_id>[^/]+)/digest-preview$")


@dataclass
class ApiResponse:
    """Structured API response for the HTTP layer and tests."""

    status_code: int
    payload: dict

    def to_http(self) -> tuple[int, bytes, list[tuple[str, str]]]:
        body = json.dumps(self.payload, ensure_ascii=False).encode("utf-8")
        headers = [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(body))),
        ]
        return self.status_code, body, headers


def _json_response(status_code: int, payload: dict) -> ApiResponse:
    return ApiResponse(status_code=status_code, payload=payload)


def _ok(payload: dict) -> ApiResponse:
    return _json_response(200, payload)


def _created(payload: dict) -> ApiResponse:
    return _json_response(201, payload)


def _bad_request(message: str) -> ApiResponse:
    return _json_response(400, {"error": message})


def _not_found() -> ApiResponse:
    return _json_response(404, {"error": "Not found"})


def _parse_json_body(body: bytes) -> dict:
    if not body:
        return {}
    try:
        data = json.loads(body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise ValueError("Invalid JSON body")
    if not isinstance(data, dict):
        raise ValueError("JSON body must be an object")
    return data


def _first_query_value(query_params: dict, key: str) -> Optional[str]:
    values = query_params.get(key)
    if not values:
        return None
    return values[0]


def handle_api_request(
    method: str,
    path: str,
    body: bytes = b"",
    env: Optional[dict] = None,
) -> ApiResponse:
    """Dispatch a JSON API request and return structured response data."""
    parsed = urlparse(path)
    route_path = parsed.path
    query_params = parse_qs(parsed.query)
    env = env or {}

    try:
        data = _parse_json_body(body)
    except ValueError as error:
        return _bad_request(str(error))

    try:
        if method == "GET" and route_path == "/health":
            return _ok({"status": "ok"})

        if method == "POST" and route_path == "/api/calc":
            if "buy_price" not in data or "sell_price" not in data:
                return _bad_request("buy_price and sell_price are required")
            payload = calculate_margin_payload(
                buy_price=float(data["buy_price"]),
                sell_price=float(data["sell_price"]),
                shipping_cost=data.get("shipping_cost"),
                packaging_cost=data.get("packaging_cost"),
                model=data.get("model", "us"),
                platform=data.get("platform", "ebay"),
            )
            return _ok(payload)

        if method == "POST" and route_path == "/api/digest-preview":
            queries = data.get("queries", [])
            if not queries:
                return _bad_request("queries are required")
            payload = asyncio.run(
                generate_digest_payload(
                    queries=queries,
                    env=env,
                    sources=data.get("sources"),
                    top=data.get("top", 10),
                    min_profit=data.get("min_profit", 5.0),
                    max_buy_price=data.get("max_buy_price"),
                    limit=data.get("limit", 20),
                    title=data.get("title"),
                )
            )
            return _ok(payload)

        match = USER_BASE_RE.match(route_path)
        if match and method == "GET":
            payload = get_user_profile_payload(
                telegram_chat_id=unquote(match.group("chat_id")),
                env=env,
                username=_first_query_value(query_params, "username"),
                preferred_language=_first_query_value(query_params, "preferred_language"),
            )
            return _ok(payload)

        match = USER_SETTINGS_RE.match(route_path)
        if match and method == "PATCH":
            payload = update_user_settings_payload(
                telegram_chat_id=unquote(match.group("chat_id")),
                env=env,
                preferred_language=data.get("preferred_language"),
                min_profit_threshold=data.get("min_profit_threshold"),
                max_buy_price=data.get("max_buy_price"),
                enabled_sources=data.get("enabled_sources"),
            )
            return _ok(payload)

        match = USER_SCHEDULE_RE.match(route_path)
        if match and method == "PATCH":
            payload = update_digest_schedule_payload(
                telegram_chat_id=unquote(match.group("chat_id")),
                interval_days=data.get("interval_days"),
                enabled=data.get("enabled", True),
                env=env,
            )
            return _ok(payload)

        match = USER_TRACKED_QUERIES_RE.match(route_path)
        if match and method == "GET":
            payload = list_tracked_queries_payload(
                telegram_chat_id=unquote(match.group("chat_id")),
                env=env,
            )
            return _ok(payload)

        if match and method == "POST":
            if "query" not in data:
                return _bad_request("query is required")
            payload = add_tracked_query_payload(
                telegram_chat_id=unquote(match.group("chat_id")),
                query=data["query"],
                env=env,
                category=data.get("category"),
                max_buy_price=data.get("max_buy_price"),
                min_profit_threshold=data.get("min_profit_threshold"),
            )
            return _created(payload)

        match = USER_TRACKED_QUERY_ITEM_RE.match(route_path)
        if match and method == "DELETE":
            payload = remove_tracked_query_payload(
                telegram_chat_id=unquote(match.group("chat_id")),
                query=unquote(match.group("query")),
                env=env,
                category=_first_query_value(query_params, "category"),
            )
            return _ok(payload)

        match = USER_DIGEST_PREVIEW_RE.match(route_path)
        if match and method == "POST":
            payload = asyncio.run(
                generate_saved_digest_payload(
                    telegram_chat_id=unquote(match.group("chat_id")),
                    env=env,
                    top=data.get("top", 10),
                    limit=data.get("limit", 20),
                    title=data.get("title"),
                )
            )
            return _ok(payload)
    except ValueError as error:
        return _bad_request(str(error))

    return _not_found()
