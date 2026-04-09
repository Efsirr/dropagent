"""Tests for the i18n translation system."""

import pytest

from i18n import clear_cache, get_language, set_language, t, SUPPORTED_LANGUAGES


class TestTranslation:
    """Core translation tests."""

    def setup_method(self):
        clear_cache()
        set_language("en")

    def test_english_default(self):
        assert t("calc.profit") == "PROFIT"
        assert t("calc.buy_price") == "Buy Price"

    def test_russian(self):
        assert t("calc.profit", lang="ru") == "ПРИБЫЛЬ"
        assert t("calc.buy_price", lang="ru") == "Цена покупки"
        assert t("common.welcome", lang="ru") == "Добро пожаловать в DropAgent!"

    def test_chinese(self):
        assert t("calc.profit", lang="zh") == "盈利"
        assert t("calc.buy_price", lang="zh") == "采购价"
        assert t("common.welcome", lang="zh") == "欢迎使用DropAgent！"

    def test_set_global_language(self):
        set_language("ru")
        assert get_language() == "ru"
        assert t("calc.loss") == "УБЫТОК"

    def test_per_call_override(self):
        """lang= parameter overrides global setting."""
        set_language("en")
        assert t("calc.profit", lang="zh") == "盈利"
        # Global unchanged
        assert t("calc.profit") == "PROFIT"

    def test_missing_key_returns_key(self):
        assert t("nonexistent.key") == "nonexistent.key"

    def test_format_variables(self):
        result = t("scanner.found", lang="en", count=42, query="airpods")
        assert "42" in result
        assert "airpods" in result

    def test_fallback_to_english(self):
        """Unknown key in ru falls back to en, then returns key."""
        assert t("nonexistent.key", lang="ru") == "nonexistent.key"

    def test_unsupported_language_raises(self):
        with pytest.raises(ValueError, match="Unsupported"):
            set_language("jp")

    def test_all_languages_have_same_keys(self):
        """All language files should have the same structure."""
        from i18n import _load_lang

        en = _load_lang("en")
        for lang in ("ru", "zh"):
            other = _load_lang(lang)
            assert set(en.keys()) == set(other.keys()), f"{lang} missing top-level keys"
            for section in en:
                assert set(en[section].keys()) == set(other[section].keys()), (
                    f"{lang}.{section} missing keys"
                )
