"""Tests for the weekly category report CLI."""

import asyncio

import weekly_report


class FakeReporter:
    def __init__(self):
        self.categories = None
        self.title = None

    async def generate_report(self, categories, title=None, generated_at=None, previous_google_results=None):
        del generated_at, previous_google_results
        self.categories = categories
        self.title = title
        return type(
            "Report",
            (),
            {"summary": lambda self: "weekly summary"},
        )()


class FakeComparator:
    def __init__(self, sources, ebay_scanner, business_model=None):
        self.sources = sources
        self.ebay_scanner = ebay_scanner
        self.business_model = business_model

    async def close(self):
        return None


class TestWeeklyReportCli:
    def test_parse_args_accepts_aliexpress_source(self):
        args = weekly_report.parse_args(["--source", "aliexpress", "--category", "anime"])

        assert args.source == ["aliexpress"]

    def test_parse_args_accepts_cj_source(self):
        args = weekly_report.parse_args(["--source", "cj", "--category", "gadgets"])

        assert args.source == ["cj"]

    def test_parse_args_requires_categories_via_runner(self):
        args = weekly_report.parse_args([])

        try:
            asyncio.run(weekly_report.run_weekly_report(args, {"EBAY_APP_ID": "test"}))
        except ValueError as error:
            assert "At least one --category is required" in str(error)
        else:
            raise AssertionError("Expected ValueError")

    def test_run_weekly_report_uses_reporter(self, monkeypatch):
        args = weekly_report.parse_args(
            [
                "--category",
                "electronics",
                "--category",
                "toys",
                "--title",
                "Weekly Winners",
            ]
        )
        reporter = FakeReporter()

        monkeypatch.setattr(weekly_report, "build_sources", lambda source_names, env=None: ["amazon"])
        monkeypatch.setattr(weekly_report, "EbayScanner", lambda app_id: f"scanner:{app_id}")
        monkeypatch.setattr(weekly_report, "PriceComparator", FakeComparator)
        monkeypatch.setattr(weekly_report, "GoogleTrendsScanner", lambda: "google")
        monkeypatch.setattr(
            weekly_report,
            "WeeklyCategoryReporter",
            lambda comparator, google_scanner, reddit_scanner, top_products, trend_limit, query_limit: reporter,
        )

        output = asyncio.run(weekly_report.run_weekly_report(args, {"EBAY_APP_ID": "test"}))

        assert output == "weekly summary"
        assert reporter.categories == ["electronics", "toys"]
        assert reporter.title == "Weekly Winners"
