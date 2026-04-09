"""Tests for the eBay listing generator."""

from agent.listings import EBAY_TITLE_LIMIT, bulk_generate_listings, generate_listing


class TestGenerateListing:
    def test_generates_title_within_ebay_limit(self):
        draft = generate_listing("Apple AirPods Pro 2nd Generation Wireless Earbuds")

        assert draft.product_name == "Apple AirPods Pro 2nd Generation Wireless Earbuds"
        assert len(draft.title) <= EBAY_TITLE_LIMIT
        assert "AirPods" in draft.title

    def test_suggests_audio_category_and_specifics(self):
        draft = generate_listing("Sony Wireless Headphones")

        assert "Portable Audio" in draft.category
        assert draft.item_specifics["Connectivity"] == "Bluetooth"
        assert draft.item_specifics["Brand"] == "Sony"

    def test_extracts_name_from_url(self):
        draft = generate_listing("https://example.com/products/airpods-pro-2")

        assert draft.product_name == "airpods pro 2"
        assert "airpods pro 2" in draft.title.lower()

    def test_summary_contains_listing_labels(self):
        draft = generate_listing("LEGO Star Wars Set")

        summary = draft.summary()

        assert "EBAY LISTING DRAFT" in summary
        assert "Suggested Category" in summary
        assert "Bullet Points" in summary


class TestBulkGenerateListings:
    def test_bulk_generate_multiple_products(self):
        drafts = bulk_generate_listings(["airpods pro", "gaming mouse"])

        assert len(drafts) == 2
        assert drafts[0].product_name == "airpods pro"
        assert drafts[1].product_name == "gaming mouse"

    def test_bulk_generate_empty_list(self):
        assert bulk_generate_listings([]) == []
