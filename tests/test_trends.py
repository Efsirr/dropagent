"""Tests for the Google Trends scanner."""

from datetime import datetime

from agent.trends import (
    DEFAULT_CATEGORY_KEYWORDS,
    DEFAULT_REDDIT_SUBREDDITS,
    GoogleTrendsScanner,
    RedditTrendResult,
    RedditTrendSignal,
    RedditTrendsScanner,
    TrendKeyword,
    TrendScanResult,
    merge_trend_results,
)


class FakePytrendsClient:
    def __init__(self, related_queries_payload):
        self.related_queries_payload = related_queries_payload
        self.payload_calls = []

    def build_payload(self, kw_list, cat=0, timeframe="now 7-d", geo="US"):
        self.payload_calls.append(
            {
                "kw_list": kw_list,
                "cat": cat,
                "timeframe": timeframe,
                "geo": geo,
            }
        )

    def related_queries(self):
        return self.related_queries_payload


class FakeRedditPost:
    def __init__(self, title, score, num_comments, upvote_ratio, awards=0, url="https://reddit.test/post"):
        self.title = title
        self.score = score
        self.num_comments = num_comments
        self.upvote_ratio = upvote_ratio
        self.total_awards_received = awards
        self.url = url


class FakeSubreddit:
    def __init__(self, posts):
        self.posts = posts
        self.calls = []

    def hot(self, limit=10):
        self.calls.append(("hot", limit))
        return self.posts[:limit]

    def new(self, limit=10):
        self.calls.append(("new", limit))
        return self.posts[:limit]


class FakeRedditClient:
    def __init__(self, subreddits):
        self.subreddits = subreddits

    def subreddit(self, name):
        return self.subreddits[name]


class TestTrendKeyword:
    def test_to_dict(self):
        keyword = TrendKeyword(keyword="wireless earbuds", score=240.0, category="audio")

        data = keyword.to_dict()

        assert data["keyword"] == "wireless earbuds"
        assert data["score"] == 240.0
        assert data["category"] == "audio"


class TestTrendScanResult:
    def test_summary_empty(self):
        result = TrendScanResult(category="electronics", keywords=[], generated_at=datetime(2026, 4, 9, 9, 0))

        summary = result.summary()

        assert "No rising trends found" in summary

    def test_summary_russian(self):
        result = TrendScanResult(
            category="electronics",
            keywords=[TrendKeyword(keyword="airpods sale", score=120.0, category="electronics")],
            generated_at=datetime(2026, 4, 9, 9, 0),
        )

        summary = result.summary(lang="ru")

        assert "Категория" in summary
        assert "Оценка" in summary


class TestRedditTrendResult:
    def test_summary_empty(self):
        result = RedditTrendResult(category="gaming", signals=[], generated_at=datetime(2026, 4, 9, 9, 0))

        summary = result.summary()

        assert "No Reddit hype signals found" in summary

    def test_to_dict(self):
        result = RedditTrendResult(
            category="gaming",
            signals=[
                RedditTrendSignal(
                    title="Switch 2 rumors are everywhere",
                    subreddit="gaming",
                    score=412.0,
                    url="https://reddit.test/r/gaming/1",
                    keyword="switch",
                )
            ],
            generated_at=datetime(2026, 4, 9, 9, 0),
        )

        data = result.to_dict()

        assert data["category"] == "gaming"
        assert data["signals"][0]["subreddit"] == "gaming"


class TestGoogleTrendsScanner:
    def test_category_keywords_returns_configured_seeds(self):
        scanner = GoogleTrendsScanner(client=FakePytrendsClient({}))

        assert scanner.category_keywords("electronics") == DEFAULT_CATEGORY_KEYWORDS["electronics"]

    def test_scan_category_requires_keywords(self):
        scanner = GoogleTrendsScanner(client=FakePytrendsClient({}))

        try:
            scanner.scan_category("electronics", [])
        except ValueError as error:
            assert "At least one keyword is required" in str(error)
        else:
            raise AssertionError("Expected ValueError")

    def test_scan_category_parses_and_ranks_rising_queries(self):
        client = FakePytrendsClient(
            {
                "airpods": {
                    "rising": [
                        {"query": "airpods pro 2", "value": 250},
                        {"query": "best wireless earbuds", "value": 180},
                    ]
                },
                "earbuds": {
                    "rising": [
                        {"query": "best wireless earbuds", "value": 220},
                        {"query": "bluetooth earbuds", "value": 150},
                    ]
                },
            }
        )
        scanner = GoogleTrendsScanner(client=client)

        result = scanner.scan_category(
            category="electronics",
            keywords=["airpods", "earbuds"],
            geo="US",
            timeframe="now 7-d",
            limit=2,
        )

        assert client.payload_calls == [
            {
                "kw_list": ["airpods", "earbuds"],
                "cat": 0,
                "timeframe": "now 7-d",
                "geo": "US",
            }
        ]
        assert result.category == "electronics"
        assert result.count == 2
        assert result.keywords[0].keyword == "airpods pro 2"
        assert result.keywords[0].score == 250.0
        assert result.keywords[1].keyword == "best wireless earbuds"
        assert result.keywords[1].score == 220.0

    def test_scan_category_skips_invalid_rows(self):
        client = FakePytrendsClient(
            {
                "lego": {
                    "rising": [
                        {"query": "", "value": 100},
                        {"query": "lego star wars", "value": "breakout"},
                        {"query": "lego set", "value": 90},
                    ]
                }
            }
        )
        scanner = GoogleTrendsScanner(client=client)

        result = scanner.scan_category(category="toys", keywords=["lego"])

        assert result.count == 1
        assert result.keywords[0].keyword == "lego set"

    def test_missing_pytrends_dependency_raises(self, monkeypatch):
        scanner = GoogleTrendsScanner(client=None)
        monkeypatch.setattr("agent.trends.TrendReq", None)

        try:
            scanner.scan_category(category="electronics", keywords=["airpods"])
        except ValueError as error:
            assert "pytrends is required" in str(error)
        else:
            raise AssertionError("Expected ValueError")

    def test_scan_configured_categories(self):
        client = FakePytrendsClient(
            {
                "airpods": {"rising": [{"query": "airpods max", "value": 120}]},
                "gaming mouse": {"rising": []},
                "wireless earbuds": {"rising": []},
                "nintendo switch": {"rising": [{"query": "switch 2 leaks", "value": 200}]},
                "ps5 accessories": {"rising": []},
                "gaming headset": {"rising": []},
            }
        )
        scanner = GoogleTrendsScanner(client=client)

        results = scanner.scan_categories(["electronics", "gaming"], limit=5)

        assert len(results) == 2
        assert results[0].category == "electronics"
        assert results[1].category == "gaming"
        assert results[0].keywords[0].keyword == "airpods max"
        assert results[1].keywords[0].keyword == "switch 2 leaks"


class TestMergeTrendResults:
    def test_merge_trend_results_ranks_and_deduplicates(self):
        results = [
            TrendScanResult(
                category="electronics",
                keywords=[
                    TrendKeyword(keyword="airpods max", score=150.0, category="electronics"),
                    TrendKeyword(keyword="switch 2 leaks", score=110.0, category="electronics"),
                ],
                generated_at=datetime(2026, 4, 9, 9, 0),
            ),
            TrendScanResult(
                category="gaming",
                keywords=[
                    TrendKeyword(keyword="switch 2 leaks", score=200.0, category="gaming"),
                    TrendKeyword(keyword="ps5 controller", score=90.0, category="gaming"),
                ],
                generated_at=datetime(2026, 4, 9, 10, 0),
            ),
        ]

        merged = merge_trend_results(results, limit=2)

        assert merged.category == "combined"
        assert merged.count == 2
        assert merged.keywords[0].keyword == "switch 2 leaks"
        assert merged.keywords[0].score == 200.0
        assert merged.keywords[1].keyword == "airpods max"


class TestRedditTrendsScanner:
    def test_category_subreddits_returns_configured_list(self):
        scanner = RedditTrendsScanner(client=FakeRedditClient({}))

        assert scanner.category_subreddits("gaming") == DEFAULT_REDDIT_SUBREDDITS["gaming"]

    def test_score_post_uses_engagement_signals(self):
        scanner = RedditTrendsScanner(client=FakeRedditClient({}))
        post = FakeRedditPost(
            title="Great post",
            score=100,
            num_comments=30,
            upvote_ratio=0.9,
            awards=2,
        )

        score = scanner.score_post(post)

        assert score == 300.0

    def test_scan_category_filters_and_ranks_posts(self):
        client = FakeRedditClient(
            {
                "gaming": FakeSubreddit(
                    [
                        FakeRedditPost("Nintendo Switch 2 rumors explode", 120, 40, 0.95),
                        FakeRedditPost("Old PS4 discussion", 80, 10, 0.8),
                    ]
                ),
                "ps5": FakeSubreddit(
                    [
                        FakeRedditPost("Switch 2 leak roundup", 90, 35, 0.92),
                        FakeRedditPost("Completely unrelated thread", 300, 100, 0.99),
                    ]
                ),
                "nintendoswitch": FakeSubreddit([]),
            }
        )
        scanner = RedditTrendsScanner(client=client)

        result = scanner.scan_category(
            category="gaming",
            keywords=["switch 2"],
            subreddits=["gaming", "ps5", "nintendoswitch"],
            limit=3,
        )

        assert result.category == "gaming"
        assert result.count == 2
        assert result.signals[0].title == "Nintendo Switch 2 rumors explode"
        assert result.signals[1].title == "Switch 2 leak roundup"
        assert result.signals[0].score > result.signals[1].score

    def test_scan_category_supports_new_sort(self):
        subreddit = FakeSubreddit(
            [FakeRedditPost("AirPods deal discussion", 50, 15, 0.9)]
        )
        scanner = RedditTrendsScanner(
            client=FakeRedditClient({"headphones": subreddit})
        )

        result = scanner.scan_category(
            category="electronics",
            keywords=["airpods"],
            subreddits=["headphones"],
            sort="new",
        )

        assert result.count == 1
        assert subreddit.calls == [("new", 10)]

    def test_missing_praw_dependency_raises(self, monkeypatch):
        scanner = RedditTrendsScanner(client=None)
        monkeypatch.setattr("agent.trends.praw", None)

        try:
            scanner.scan_category(category="gaming", keywords=["switch"])
        except ValueError as error:
            assert "praw is required" in str(error)
        else:
            raise AssertionError("Expected ValueError")
