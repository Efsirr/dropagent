"""
eBay listing generator for DropAgent.

Builds listing drafts from a product name or URL with optimized titles,
descriptions, bullet points, category suggestions, and item specifics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import unquote, urlparse

from i18n import t


EBAY_TITLE_LIMIT = 80

CATEGORY_RULES = [
    {
        "keywords": ("airpods", "earbuds", "headphones", "headset"),
        "category": "Consumer Electronics > Portable Audio & Headphones > Headphones",
        "item_specifics": {
            "Type": "Earbud (In Ear)",
            "Connectivity": "Bluetooth",
            "Wireless Technology": "Bluetooth",
        },
    },
    {
        "keywords": ("mouse", "keyboard", "controller"),
        "category": "Computers/Tablets & Networking > Keyboards, Mice & Pointers",
        "item_specifics": {
            "Connectivity": "Wireless",
            "Type": "Standard",
        },
    },
    {
        "keywords": ("lego", "pokemon", "hot wheels", "toy"),
        "category": "Toys & Hobbies > Action Figures & Accessories",
        "item_specifics": {
            "Age Level": "8+",
        },
    },
    {
        "keywords": ("air fryer", "vacuum", "desk", "home"),
        "category": "Home & Garden > Household Supplies & Cleaning",
        "item_specifics": {
            "Room": "Any Room",
        },
    },
]


def _clean_input(value: str) -> str:
    return " ".join(value.replace("_", " ").replace("-", " ").split())


def _product_name_from_input(value: str) -> str:
    """Extract a displayable product name from a plain string or URL."""
    value = value.strip()
    if not value:
        raise ValueError("Product name cannot be empty")

    parsed = urlparse(value)
    if parsed.scheme and parsed.netloc:
        path = unquote(parsed.path.strip("/"))
        candidate = path.split("/")[-1] if path else parsed.netloc
        return _clean_input(candidate) or value
    return _clean_input(value)


def _guess_brand(product_name: str) -> Optional[str]:
    first_word = product_name.split()[0] if product_name.split() else None
    if not first_word:
        return None
    if first_word.lower() in {"new", "wireless", "bluetooth"}:
        return None
    return first_word.title()


def _suggest_category(product_name: str) -> tuple[str, dict[str, str]]:
    lowered = product_name.lower()
    for rule in CATEGORY_RULES:
        if any(keyword in lowered for keyword in rule["keywords"]):
            return rule["category"], dict(rule["item_specifics"])
    return (
        "Consumer Electronics > Other Consumer Electronics",
        {"Condition": "New"},
    )


def _optimize_title(product_name: str, category: str) -> str:
    tokens = []
    category_hint = []

    if "Portable Audio" in category:
        category_hint = ["Wireless", "Bluetooth", "New"]
    elif "Keyboards, Mice" in category:
        category_hint = ["Fast", "Shipping", "New"]
    elif "Toys & Hobbies" in category:
        category_hint = ["Gift", "Idea", "New"]
    else:
        category_hint = ["Fast", "Shipping", "New"]

    for token in (product_name.split() + category_hint):
        normalized = token.strip()
        if not normalized:
            continue
        if normalized.lower() not in {item.lower() for item in tokens}:
            tokens.append(normalized)

    title = " ".join(tokens)
    if len(title) <= EBAY_TITLE_LIMIT:
        return title

    shortened = []
    current_length = 0
    for token in tokens:
        projected = current_length + len(token) + (1 if shortened else 0)
        if projected > EBAY_TITLE_LIMIT:
            break
        shortened.append(token)
        current_length = projected
    return " ".join(shortened)


@dataclass
class ListingDraft:
    """Generated eBay listing draft."""

    source_input: str
    product_name: str
    title: str
    description: str
    bullet_points: list[str]
    category: str
    item_specifics: dict[str, str]
    suggested_price_note: str = "Review current sold listings before publishing."

    def to_dict(self) -> dict:
        return {
            "source_input": self.source_input,
            "product_name": self.product_name,
            "title": self.title,
            "description": self.description,
            "bullet_points": self.bullet_points,
            "category": self.category,
            "item_specifics": self.item_specifics,
            "suggested_price_note": self.suggested_price_note,
        }

    def summary(self, lang: Optional[str] = None) -> str:
        sep = "=" * 50
        lines = [
            sep,
            f"  {t('listing.title', lang=lang)}",
            sep,
            f"  {t('listing.product_name', lang=lang)}: {self.product_name}",
            f"  {t('listing.ebay_title', lang=lang)}: {self.title}",
            f"  {t('listing.category', lang=lang)}: {self.category}",
            f"  {t('listing.bullets', lang=lang)}:",
        ]
        for bullet in self.bullet_points:
            lines.append(f"  - {bullet}")
        lines.append(f"  {t('listing.price_note', lang=lang)}: {self.suggested_price_note}")
        lines.append(sep)
        return "\n".join(lines)


def generate_listing(product_input: str) -> ListingDraft:
    """Generate a single eBay listing draft."""
    product_name = _product_name_from_input(product_input)
    brand = _guess_brand(product_name)
    category, item_specifics = _suggest_category(product_name)

    item_specifics.setdefault("Brand", brand or "Unbranded")
    item_specifics.setdefault("Condition", "New")
    item_specifics.setdefault("MPN", "Does Not Apply")

    bullet_points = [
        f"Optimized for buyers searching for {product_name}.",
        "Clean title and specifics designed for marketplace visibility.",
        "Fast shipping friendly wording suitable for resale listings.",
    ]
    description = (
        f"{product_name}\n\n"
        "Includes the core product only unless otherwise stated.\n"
        "Please review all photos, specifics, and compatibility details before purchase."
    )

    return ListingDraft(
        source_input=product_input,
        product_name=product_name,
        title=_optimize_title(product_name, category),
        description=description,
        bullet_points=bullet_points,
        category=category,
        item_specifics=item_specifics,
    )


def bulk_generate_listings(product_inputs: list[str]) -> list[ListingDraft]:
    """Generate listing drafts for multiple products."""
    if not product_inputs:
        return []
    return [generate_listing(product_input) for product_input in product_inputs]
