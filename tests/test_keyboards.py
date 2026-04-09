"""Tests for bot.keyboards — Telegram keyboard layouts."""

from __future__ import annotations

import pytest

from bot.keyboards import (
    main_menu_keyboard,
    settings_reply_keyboard,
    remove_keyboard,
    onboarding_welcome_keyboard,
    onboarding_model_keyboard,
    onboarding_integrations_keyboard,
    language_inline_keyboard,
    settings_inline_keyboard,
    schedule_inline_keyboard,
    confirm_inline_keyboard,
    tracked_query_inline_keyboard,
    export_inline_keyboard,
    sources_inline_keyboard,
)


# ---------------------------------------------------------------------------
# Reply Keyboard tests
# ---------------------------------------------------------------------------


class TestMainMenuKeyboard:
    """Tests for the main menu reply keyboard."""

    def test_has_keyboard_key(self):
        kb = main_menu_keyboard()
        assert "keyboard" in kb

    def test_has_resize(self):
        kb = main_menu_keyboard()
        assert kb["resize_keyboard"] is True

    def test_has_expected_commands(self):
        kb = main_menu_keyboard()
        flat = [btn["text"] for row in kb["keyboard"] for btn in row]
        assert any("/digest" in t for t in flat)
        assert any("/calc" in t for t in flat)
        assert any("/settings" in t for t in flat)
        assert any("/help" in t for t in flat)

    def test_has_multiple_rows(self):
        kb = main_menu_keyboard()
        assert len(kb["keyboard"]) >= 3


class TestSettingsReplyKeyboard:
    """Tests for the settings sub-menu reply keyboard."""

    def test_has_settings_commands(self):
        kb = settings_reply_keyboard()
        flat = [btn["text"] for row in kb["keyboard"] for btn in row]
        assert any("/language" in t for t in flat)
        assert any("/minprofit" in t for t in flat)
        assert any("/maxbuy" in t for t in flat)
        assert any("/sources" in t for t in flat)
        assert any("/schedule" in t for t in flat)


class TestRemoveKeyboard:
    """Tests for keyboard removal."""

    def test_remove_keyboard(self):
        kb = remove_keyboard()
        assert kb["remove_keyboard"] is True


# ---------------------------------------------------------------------------
# Inline Keyboard tests
# ---------------------------------------------------------------------------


class TestLanguageInlineKeyboard:
    """Tests for the language picker inline keyboard."""

    def test_has_inline_keyboard(self):
        kb = language_inline_keyboard()
        assert "inline_keyboard" in kb

    def test_has_three_languages(self):
        kb = language_inline_keyboard()
        buttons = kb["inline_keyboard"][0]
        assert len(buttons) == 3

    def test_callback_data_format(self):
        kb = language_inline_keyboard()
        buttons = kb["inline_keyboard"][0]
        callbacks = [b["callback_data"] for b in buttons]
        assert "lang:en" in callbacks
        assert "lang:ru" in callbacks
        assert "lang:zh" in callbacks


class TestOnboardingKeyboards:
    def test_welcome_keyboard_has_begin_and_skip(self):
        kb = onboarding_welcome_keyboard()
        callbacks = [btn["callback_data"] for row in kb["inline_keyboard"] for btn in row]

        assert "onboarding:start" in callbacks
        assert "onboarding:skip" in callbacks

    def test_model_keyboard_has_both_modes(self):
        kb = onboarding_model_keyboard()
        callbacks = [btn["callback_data"] for row in kb["inline_keyboard"] for btn in row]

        assert "onboarding:model:us_arbitrage" in callbacks
        assert "onboarding:model:china_dropshipping" in callbacks

    def test_integrations_keyboard_switches_by_model(self):
        us = onboarding_integrations_keyboard(business_model="us_arbitrage")
        china = onboarding_integrations_keyboard(business_model="china_dropshipping")

        us_callbacks = [row[0]["callback_data"] for row in us["inline_keyboard"][:-1]]
        china_callbacks = [row[0]["callback_data"] for row in china["inline_keyboard"][:-1]]

        assert "onboarding:toggle:keepa" in us_callbacks
        assert "onboarding:toggle:zik" in us_callbacks
        assert "onboarding:toggle:aliexpress" in china_callbacks
        assert "onboarding:toggle:cj" in china_callbacks


class TestSettingsInlineKeyboard:
    """Tests for the settings inline keyboard."""

    def test_has_setting_callbacks(self):
        kb = settings_inline_keyboard()
        all_callbacks = [
            btn["callback_data"]
            for row in kb["inline_keyboard"]
            for btn in row
        ]
        assert "settings:language" in all_callbacks
        assert "settings:minprofit" in all_callbacks
        assert "settings:schedule" in all_callbacks

    def test_uses_i18n_labels(self):
        kb = settings_inline_keyboard(lang="en")
        all_text = [
            btn["text"]
            for row in kb["inline_keyboard"]
            for btn in row
        ]
        # Should contain translated text, not raw keys
        assert all(not t.startswith("settings.") for t in all_text)


class TestScheduleInlineKeyboard:
    """Tests for the schedule picker inline keyboard."""

    def test_has_schedule_options(self):
        kb = schedule_inline_keyboard()
        all_callbacks = [
            btn["callback_data"]
            for row in kb["inline_keyboard"]
            for btn in row
        ]
        assert "schedule:off" in all_callbacks
        assert "schedule:1" in all_callbacks
        assert "schedule:weekly" in all_callbacks


class TestConfirmInlineKeyboard:
    """Tests for the generic confirmation keyboard."""

    def test_confirm_with_action(self):
        kb = confirm_inline_keyboard("delete")
        buttons = kb["inline_keyboard"][0]
        assert len(buttons) == 2
        assert buttons[0]["callback_data"] == "delete:yes"
        assert buttons[1]["callback_data"] == "delete:no"

    def test_confirm_with_item_id(self):
        kb = confirm_inline_keyboard("untrack", item_id="airpods")
        buttons = kb["inline_keyboard"][0]
        assert buttons[0]["callback_data"] == "untrack:yes:airpods"


class TestTrackedQueryInlineKeyboard:
    """Tests for the tracked query remove buttons."""

    def test_generates_buttons_from_dicts(self):
        queries = [
            {"query": "airpods pro"},
            {"query": "gaming mouse"},
        ]
        kb = tracked_query_inline_keyboard(queries)
        assert len(kb["inline_keyboard"]) == 2
        assert kb["inline_keyboard"][0][0]["callback_data"] == "untrack:airpods pro"

    def test_limits_to_10(self):
        queries = [{"query": f"product_{i}"} for i in range(15)]
        kb = tracked_query_inline_keyboard(queries)
        assert len(kb["inline_keyboard"]) == 10

    def test_handles_objects_with_query_attr(self):
        class FakeQuery:
            def __init__(self, q):
                self.query = q
        queries = [FakeQuery("test")]
        kb = tracked_query_inline_keyboard(queries)
        assert kb["inline_keyboard"][0][0]["callback_data"] == "untrack:test"


class TestExportInlineKeyboard:
    """Tests for the export action keyboard."""

    def test_has_export_options(self):
        kb = export_inline_keyboard()
        all_callbacks = [
            btn["callback_data"]
            for row in kb["inline_keyboard"]
            for btn in row
        ]
        assert "export:sheets" in all_callbacks
        assert "export:email" in all_callbacks
        assert "export:discord" in all_callbacks


class TestSourcesInlineKeyboard:
    """Tests for the sources toggle keyboard."""

    def test_shows_all_sources(self):
        kb = sources_inline_keyboard()
        texts = [row[0]["text"] for row in kb["inline_keyboard"][:-1]]

        assert any("Amazon" in text for text in texts)
        assert any("Walmart" in text for text in texts)
        assert any("AliExpress" in text for text in texts)
        assert any("CJDropshipping" in text for text in texts)

    def test_shows_checkmarks_for_active(self):
        kb = sources_inline_keyboard(current_sources=["amazon", "aliexpress"])
        texts = [row[0]["text"] for row in kb["inline_keyboard"]]

        assert any("✅" in t and "Amazon" in t for t in texts)
        assert any("⬜" in t and "Walmart" in t for t in texts)
        assert any("✅" in t and "AliExpress" in t for t in texts)
        assert any("⬜" in t and "CJDropshipping" in t for t in texts)

    def test_uses_expected_callback_ids_for_model2_sources(self):
        kb = sources_inline_keyboard()
        callbacks = [row[0]["callback_data"] for row in kb["inline_keyboard"]]

        assert "source_toggle:aliexpress" in callbacks
        assert "source_toggle:cj" in callbacks

    def test_save_button_present(self):
        kb = sources_inline_keyboard()
        last_row = kb["inline_keyboard"][-1]
        assert last_row[0]["callback_data"] == "source_toggle:save"
