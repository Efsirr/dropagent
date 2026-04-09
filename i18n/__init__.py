"""
DropAgent i18n — Internationalization module.

Supports: English (en), Russian (ru), Chinese (zh).
English is the default fallback language.

Usage:
    from i18n import t, set_language

    set_language("ru")
    print(t("calc.profit"))       # "ПРИБЫЛЬ"
    print(t("calc.buy_price"))    # "Цена покупки"

    # Per-user language (thread-safe):
    print(t("calc.profit", lang="zh"))  # "盈利"
"""

import json
from pathlib import Path
from typing import Optional

_LANG_DIR = Path(__file__).parent
_DEFAULT_LANG = "en"
_current_lang = _DEFAULT_LANG
_cache: dict[str, dict] = {}

SUPPORTED_LANGUAGES = ("en", "ru", "zh")


def _load_lang(lang: str) -> dict:
    """Load and cache a language file."""
    if lang in _cache:
        return _cache[lang]

    lang_file = _LANG_DIR / f"{lang}.json"
    if not lang_file.exists():
        if lang != _DEFAULT_LANG:
            return _load_lang(_DEFAULT_LANG)
        raise FileNotFoundError(f"Default language file not found: {lang_file}")

    with open(lang_file, "r", encoding="utf-8") as f:
        _cache[lang] = json.load(f)
    return _cache[lang]


def _resolve_key(data: dict, key: str) -> Optional[str]:
    """Resolve a dotted key like 'calc.buy_price' from nested dict."""
    parts = key.split(".")
    current = data
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current if isinstance(current, str) else None


def set_language(lang: str) -> None:
    """Set the global default language."""
    global _current_lang
    if lang not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language: {lang}. Use one of: {SUPPORTED_LANGUAGES}")
    _current_lang = lang


def get_language() -> str:
    """Get the current global language."""
    return _current_lang


def t(key: str, lang: Optional[str] = None, **kwargs) -> str:
    """
    Translate a key to the current (or specified) language.

    Args:
        key: Dotted key path, e.g. "calc.net_profit".
        lang: Override language for this call.
        **kwargs: Format variables, e.g. t("calc.result", amount="10.24").

    Returns:
        Translated string, or the key itself if not found.
    """
    lang = lang or _current_lang

    # Try requested language
    data = _load_lang(lang)
    result = _resolve_key(data, key)

    # Fallback to English
    if result is None and lang != _DEFAULT_LANG:
        data = _load_lang(_DEFAULT_LANG)
        result = _resolve_key(data, key)

    # Last resort: return the key
    if result is None:
        return key

    if kwargs:
        result = result.format(**kwargs)

    return result


def clear_cache() -> None:
    """Clear loaded translations (useful for testing)."""
    _cache.clear()
