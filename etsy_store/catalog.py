#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
קטלוג קולקציית חג המולד - Line Art Pets
========================================
מגדיר גזעים × מוצרים ומייצר לכל מודעה כותרת, תיאור ו-13 תגיות ל-Etsy.

הרצה:
  python catalog.py            # יוצר listings.csv
"""

import csv
from pathlib import Path

# ─── הגדרות - שנה לפי הצורך ────────────────────────────────────────────────
SHOP_NAME = "PawLine Studio"
YEAR      = "2026"
OUTPUT    = Path(__file__).with_name("listings.csv")
# ────────────────────────────────────────────────────────────────────────────

# key → (שם תצוגה, כינויים לחיפוש, חיה, ברכה)
BREEDS = {
    "dachshund":      ("Dachshund", ["doxie", "wiener dog", "sausage dog"], "dog", "Merry Woofmas"),
    "french_bulldog": ("French Bulldog", ["frenchie", "frenchie mom", "bulldog"], "dog", "Merry Woofmas"),
    "golden":         ("Golden Retriever", ["golden", "golden mom", "retriever"], "dog", "Merry Woofmas"),
    "labrador":       ("Labrador", ["lab", "black lab", "lab mom"], "dog", "Merry Woofmas"),
    "corgi":          ("Corgi", ["corgi mom", "pembroke corgi", "corgi lover"], "dog", "Merry Woofmas"),
    "doodle":         ("Goldendoodle", ["doodle", "doodle mom", "poodle mix"], "dog", "Merry Woofmas"),
    "cat":            ("Cat", ["kitty", "cat mom", "cat lover"], "cat", "Meowy Christmas"),
}

# key → הגדרות מוצר. price בסנטים. blueprint_query משמש את printify_sync.py
# כדי למצוא את המוצר בקטלוג של Printify (לא מנחשים מזהים).
PRODUCTS = {
    "ornament": {
        "noun": "Christmas Ornament", "price": 2200,
        "blueprint_query": "ceramic ornament",
        "extra_tags": ["ornament {year}", "custom ornament", "first christmas"],
    },
    "stocking": {
        "noun": "Christmas Stocking", "price": 3200,
        "blueprint_query": "stocking",
        "extra_tags": ["pet stocking", "name stocking", "christmas decor"],
    },
    "mug": {
        "noun": "Christmas Mug", "price": 2600,
        "blueprint_query": "mug 11oz",
        "extra_tags": ["christmas mug", "custom mug", "coffee mug gift"],
    },
    "blanket": {
        "noun": "Christmas Blanket", "price": 5900,
        "blueprint_query": "fleece blanket",
        "extra_tags": ["custom blanket", "holiday blanket", "cozy gift"],
    },
    "bandana": {
        "noun": "Christmas Bandana", "price": 1800,
        "blueprint_query": "pet bandana",
        "extra_tags": ["dog bandana", "holiday bandana", "pet accessory"],
    },
    "pillow": {
        "noun": "Christmas Pillow", "price": 3500,
        "blueprint_query": "spun polyester square pillow",
        "extra_tags": ["throw pillow", "holiday decor", "custom pillow"],
    },
}

# מוצרים דיגיטליים - מועלים ידנית ב-Etsy (Printify לא מטפל בהם)
DIGITAL = [
    ("christmas_card", "Editable Pet Christmas Card Template, Line Art Dog Holiday Card, Canva Template", 700),
    ("gift_tags", "Printable From the Dog Gift Tags, Christmas Pet Gift Tags, Instant Download", 450),
    ("santa_letter", "Printable Letter to Santa From the Dog, Funny Pet Christmas Printable", 450),
]


def _tags(breed_key, product_key):
    name, aliases, animal, _ = BREEDS[breed_key]
    product = PRODUCTS[product_key]
    tags = [
        f"{name.lower()} {product_key}",
        f"{aliases[0]} christmas",
        f"custom {animal} {product_key}",
        f"{animal} name gift",
        f"{aliases[1]} gift",
        f"{animal} mom gift",
        f"line art {animal}",
        "minimalist gift",
        "personalized pet",
        f"{animal} christmas {YEAR}",
    ] + [t.format(year=YEAR) for t in product["extra_tags"]]
    # Etsy: עד 13 תגיות, כל אחת עד 20 תווים, בלי כפילויות
    seen, result = set(), []
    for t in tags:
        t = t[:20].strip()
        if t not in seen:
            seen.add(t)
            result.append(t)
    return result[:13]


def _title(breed_key, product_key):
    name, aliases, animal, greeting = BREEDS[breed_key]
    noun = PRODUCTS[product_key]["noun"]
    title = (f"Personalized {name} {noun} {YEAR}, Custom {animal.title()} Name {noun.split()[-1]}, "
             f"Minimalist Line Art, {animal.title()} Mom Gift, {aliases[0].title()} {greeting}")
    return title[:140]  # מגבלת Etsy


def _description(breed_key, product_key):
    name, _, animal, greeting = BREEDS[breed_key]
    noun = PRODUCTS[product_key]["noun"].lower()
    return (
        f"{greeting}! A minimalist line art {name} {noun}, personalized with your {animal}'s name.\n\n"
        f"HOW TO ORDER\n"
        f"1. Choose your options\n"
        f"2. Add your {animal}'s name in the personalization box (max 12 characters)\n"
        f"3. Add to cart - we'll handle the rest\n\n"
        f"Made to order just for you and shipped from our production partner.\n"
        f"Order by our holiday cutoff date (see shop announcement) for delivery before Christmas.\n\n"
        f"Designed by {SHOP_NAME}."
    )


def build_listings():
    rows = []
    for b in BREEDS:
        for p, cfg in PRODUCTS.items():
            rows.append({
                "sku": f"{b}-{p}",
                "breed": b,
                "product": p,
                "type": "pod",
                "title": _title(b, p),
                "price_usd": f"{cfg['price'] / 100:.2f}",
                "tags": ", ".join(_tags(b, p)),
                "description": _description(b, p),
                "design_file": f"designs/{b}.png",
            })
    for key, title, price in DIGITAL:
        rows.append({
            "sku": f"digital-{key}", "breed": "", "product": key, "type": "digital",
            "title": title, "price_usd": f"{price / 100:.2f}", "tags": "",
            "description": "", "design_file": f"designs/digital/{key}.pdf",
        })
    return rows


def main():
    rows = build_listings()
    with OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"נכתבו {len(rows)} מודעות אל {OUTPUT}")


if __name__ == "__main__":
    main()
