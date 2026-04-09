"""Tests for the daily digest CLI."""

from datetime import datetime

import digest
from agent.digest import build_daily_digest
from agent.scheduler import ScanRequest
from agent.sources.base import BaseSource


class FakeSource(BaseSource):
    @property
    def name(self) -> str:
        return "fake"

    async def search(
        self,
        query: str,
        category=None,
        min_price=None,
        max_price=None,
        limit: int = 20,
    ):
        del query, category, min_price, max_price, limit
        return []

    async def get_product(self, product_id: str):
        del product_id
        return None


class FakeComparator:
    def __init__(self, sources, ebay_scanner, min_profit=5.0, min_sold_count=3):
        del ebay_scanner, min_profit, min_sold_count
        self.sources = sources
        self.closed = False

    async def close(self):
        self.closed = True


class FakeScheduler:
    def __init__(self, comparator, top_n=10, min_profit=5.0):
        self.comparator = comparator
        self.top_n = top_n
        self.min_profit = min_profit
        self.last_requests = None
        self.last_title = None

    async def generate_digest(self, requests, title=None, generated_at=None):
        self.last_requests = requests
        self.last_title = title
        return build_daily_digest(
            [],
            title=title or "Test Digest",
            top_n=self.top_n,
            min_profit=self.min_profit,
            generated_at=generated_at or datetime(2026, 4, 9, 9, 0),
        )


class TestParseArgs:
    def test_parse_args_defaults(self):
        args = digest.parse_args([])

        assert args.query == []
        assert args.source == []
        assert args.top == 10
        assert args.min_profit == 5.0


class TestBuildScanRequests:
    def test_builds_from_cli_queries(self):
        args = digest.parse_args(
            ["--query", "airpods", "--query", "gaming mouse", "--limit", "7"]
        )

        requests = digest.build_scan_requests(args, {})

        assert requests == [
            ScanRequest(query="airpods", max_buy_price=None, limit=7),
            ScanRequest(query="gaming mouse", max_buy_price=None, limit=7),
        ]

    def test_builds_from_env_when_cli_missing(self):
        args = digest.parse_args(["--limit", "9", "--max-buy-price", "40"])

        requests = digest.build_scan_requests(
            args,
            {"DIGEST_QUERIES": "airpods, gaming mouse"},
        )

        assert requests == [
            ScanRequest(query="airpods", max_buy_price=40.0, limit=9),
            ScanRequest(query="gaming mouse", max_buy_price=40.0, limit=9),
        ]

    def test_raises_when_no_queries_configured(self):
        args = digest.parse_args([])

        try:
            digest.build_scan_requests(args, {})
        except ValueError as error:
            assert "No digest queries provided" in str(error)
        else:
            raise AssertionError("Expected ValueError")


class TestBuildSources:
    def test_auto_selects_configured_sources(self, monkeypatch):
        monkeypatch.setattr(digest, "AmazonSource", lambda: "amazon")
        monkeypatch.setattr(digest, "WalmartSource", lambda: "walmart")
        monkeypatch.setattr(digest, "AliExpressSource", lambda: "aliexpress")
        monkeypatch.setattr(digest, "CJDropshippingSource", lambda: "cj")

        sources = digest.build_sources(
            [],
            {
                "AMAZON_ACCESS_KEY": "a",
                "AMAZON_SECRET_KEY": "b",
                "AMAZON_PARTNER_TAG": "c",
                "WALMART_API_KEY": "w",
                "ALIEXPRESS_APP_KEY": "ak",
                "ALIEXPRESS_APP_SECRET": "as",
                "CJ_API_KEY": "cj",
            },
        )

        assert sources == ["amazon", "walmart", "aliexpress", "cj"]

    def test_requested_aliexpress_source_requires_credentials(self):
        try:
            digest.build_sources(["aliexpress"], {})
        except ValueError as error:
            assert "AliExpress source requested" in str(error)
        else:
            raise AssertionError("Expected ValueError")

    def test_requested_cj_source_requires_credentials(self):
        try:
            digest.build_sources(["cj"], {})
        except ValueError as error:
            assert "CJ source requested" in str(error)
        else:
            raise AssertionError("Expected ValueError")

    def test_requested_source_requires_credentials(self):
        try:
            digest.build_sources(["walmart"], {})
        except ValueError as error:
            assert "Walmart source requested" in str(error)
        else:
            raise AssertionError("Expected ValueError")

    def test_raises_when_no_sources_configured(self):
        try:
            digest.build_sources([], {})
        except ValueError as error:
            assert "No marketplace sources configured" in str(error)
        else:
            raise AssertionError("Expected ValueError")

    def test_infers_china_business_model_for_aliexpress(self):
        assert digest.infer_business_model(["aliexpress"]).value == "china_dropshipping"
        assert digest.infer_business_model(["amazon"]).value == "us_arbitrage"


class TestRunDigest:
    def test_requires_ebay_app_id(self):
        args = digest.parse_args(["--query", "airpods"])

        try:
            import asyncio

            asyncio.run(digest.run_digest(args, {}))
        except ValueError as error:
            assert "EBAY_APP_ID is required" in str(error)
        else:
            raise AssertionError("Expected ValueError")

    def test_run_digest_uses_scheduler(self, monkeypatch):
        args = digest.parse_args(
            [
                "--query",
                "airpods",
                "--source",
                "amazon",
                "--title",
                "Morning Report",
            ]
        )
        fake_scheduler = FakeScheduler(comparator=FakeComparator(sources=[FakeSource()], ebay_scanner=None))

        monkeypatch.setattr(digest, "build_sources", lambda source_names, env=None: [FakeSource()])
        monkeypatch.setattr(
            digest,
            "PriceComparator",
            lambda sources, ebay_scanner, min_profit=5.0, business_model=None: FakeComparator(
                sources,
                ebay_scanner,
                min_profit=min_profit,
            ),
        )
        monkeypatch.setattr(digest, "MorningDigestScheduler", lambda comparator, top_n=10, min_profit=5.0: fake_scheduler)

        import asyncio

        output = asyncio.run(digest.run_digest(args, {"EBAY_APP_ID": "test"}))

        assert "No profitable opportunities found" in output
        assert fake_scheduler.last_title == "Morning Report"
        assert fake_scheduler.last_requests == [
            ScanRequest(query="airpods", max_buy_price=None, limit=20)
        ]


class TestMain:
    def test_main_returns_error_code_on_value_error(self, monkeypatch, capsys):
        monkeypatch.setattr(digest, "load_dotenv", lambda: None)
        monkeypatch.setattr(digest, "run_digest", lambda args, env=None: (_ for _ in ()).throw(ValueError("boom")))

        exit_code = digest.main(["--query", "airpods"])

        captured = capsys.readouterr()
        assert exit_code == 1
        assert "Error: boom" in captured.err
