#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
העלאת הקטלוג ל-Printify ופרסום אוטומטי לחנות ה-Etsy המחוברת
===========================================================
דרישות:
  - חנות Etsy מחוברת לחשבון Printify (Printify → My Stores → Etsy)
  - טוקן API מ-Printify (My Account → Connections) במשתנה הסביבה PRINTIFY_API_TOKEN
  - קבצי עיצוב PNG שקופים ב-designs/<breed>.png (לפחות 4500px)

הרצה:
  python printify_sync.py --shops                  # מציג את ה-shop_id של החנות
  python printify_sync.py --find "ceramic ornament" # מחפש מוצר בקטלוג של Printify
  python printify_sync.py --shop 123 --dry-run     # מראה מה ייווצר, בלי לשנות כלום
  python printify_sync.py --shop 123 --only dachshund-ornament --publish
"""

import argparse
import base64
import json
import os
import sys
import urllib.request
from pathlib import Path

from catalog import PRODUCTS, build_listings

API   = "https://api.printify.com/v1"
HERE  = Path(__file__).parent
STATE = HERE / "printify_state.json"   # מה כבר הועלה - כדי לא ליצור כפילויות


def call(method, path, body=None):
    token = os.environ.get("PRINTIFY_API_TOKEN")
    if not token:
        sys.exit("חסר PRINTIFY_API_TOKEN במשתני הסביבה")
    req = urllib.request.Request(
        f"{API}{path}", method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "pawline-sync"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read()
    return json.loads(raw) if raw else {}


def find_blueprint(query):
    words = query.lower().split()
    return [b for b in call("GET", "/catalog/blueprints.json")
            if all(w in b["title"].lower() for w in words)]


def pick_provider_and_variants(blueprint_id):
    """הספק הראשון ברשימה וכל הווריאנטים שלו. כדאי לבדוק ידנית איזה ספק הכי טוב."""
    providers = call("GET", f"/catalog/blueprints/{blueprint_id}/print_providers.json")
    if not providers:
        raise RuntimeError(f"אין ספקים ל-blueprint {blueprint_id}")
    provider = providers[0]
    variants = call("GET", f"/catalog/blueprints/{blueprint_id}/print_providers/"
                           f"{provider['id']}/variants.json")["variants"]
    return provider, variants


def upload_image(path):
    data = base64.b64encode(path.read_bytes()).decode()
    return call("POST", "/uploads/images.json", {"file_name": path.name, "contents": data})["id"]


def load_state():
    return json.loads(STATE.read_text()) if STATE.exists() else {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shops", action="store_true", help="הצג חנויות מחוברות")
    ap.add_argument("--find", metavar="QUERY", help="חפש מוצר בקטלוג")
    ap.add_argument("--shop", type=int, help="shop_id ב-Printify")
    ap.add_argument("--only", help="sku אחד בלבד, לבדיקה")
    ap.add_argument("--publish", action="store_true", help="פרסם ל-Etsy אחרי היצירה")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.shops:
        for s in call("GET", "/shops.json"):
            print(s["id"], s["sales_channel"], s["title"])
        return
    if args.find:
        for b in find_blueprint(args.find):
            print(b["id"], b["title"], "-", b.get("brand", ""))
        return
    if not args.shop:
        ap.error("צריך --shop (הרץ קודם --shops)")

    state = load_state()
    blueprints = {}
    images = {}
    for row in build_listings():
        if row["type"] != "pod" or row["sku"] in state:
            continue
        if args.only and row["sku"] != args.only:
            continue
        design = HERE / row["design_file"]
        if args.dry_run:
            print(f"[dry-run] {row['sku']}: {row['title']} - ${row['price_usd']} "
                  f"({'יש עיצוב' if design.exists() else 'חסר ' + row['design_file']})")
            continue
        if not design.exists():
            print(f"דילוג על {row['sku']}: חסר {row['design_file']}")
            continue

        cfg = PRODUCTS[row["product"]]
        if row["product"] not in blueprints:
            matches = find_blueprint(cfg["blueprint_query"])
            if not matches:
                sys.exit(f"לא נמצא מוצר ל-'{cfg['blueprint_query']}' - עדכן blueprint_query ב-catalog.py")
            bp = matches[0]
            provider, variants = pick_provider_and_variants(bp["id"])
            print(f"{row['product']}: {bp['title']} (#{bp['id']}) אצל {provider['title']}")
            blueprints[row["product"]] = (bp["id"], provider["id"], variants)
        bp_id, provider_id, variants = blueprints[row["product"]]

        if design not in images:
            images[design] = upload_image(design)
        variant_ids = [v["id"] for v in variants]
        product = call("POST", f"/shops/{args.shop}/products.json", {
            "title": row["title"],
            "description": row["description"],
            "tags": [t.strip() for t in row["tags"].split(",")],
            "blueprint_id": bp_id,
            "print_provider_id": provider_id,
            "variants": [{"id": v, "price": cfg["price"], "is_enabled": True} for v in variant_ids],
            "print_areas": [{
                "variant_ids": variant_ids,
                "placeholders": [{"position": "front", "images": [
                    {"id": images[design], "x": 0.5, "y": 0.5, "scale": 1, "angle": 0}]}],
            }],
        })
        if args.publish:
            call("POST", f"/shops/{args.shop}/products/{product['id']}/publish.json", {
                "title": True, "description": True, "images": True, "variants": True,
                "tags": True, "keyFeatures": True, "shipping_template": True,
            })
        state[row["sku"]] = product["id"]
        STATE.write_text(json.dumps(state, indent=2))
        print(f"✓ {row['sku']} → {product['id']}{' (פורסם)' if args.publish else ''}")


if __name__ == "__main__":
    main()
