#!/usr/bin/env python3
"""
Build the Arabic Clasico brand catalog from the English scrape + translations_ar.json.

Reads:   ../clasico_scrape   (English source data & images)
         ./translations_ar.json   (Arabic names + descriptions — editable)
Writes:  ./  (this arabic-brand folder)
           catalog/products_ar.json
           catalog/collections_ar.json
           catalog/products_index_ar.csv     (Salla-friendly, Arabic)
           products/<handle>/product_ar.json
           products/<handle>/details_ar.md
           collections/<handle>_ar.json
           indexes/by_collection_ar.json

Names are transliterated to Arabic; descriptions fully translated (MSA).
Brand word 'Clasico' is kept. Images are referenced from the source scrape
(not duplicated). Re-run any time after editing translations_ar.json.
"""

from __future__ import annotations

import csv
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(HERE, "..", "clasico_scrape"))
TRANS = os.path.join(HERE, "translations_ar.json")


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)


def desc_to_html(text: str) -> str:
    """Turn the plain Arabic description into RTL HTML for Salla."""
    blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
    parts = []
    for b in blocks:
        lines = [html.escape(x) for x in b.split("\n")]
        parts.append("<p>" + "<br>".join(lines) + "</p>")
    return '<div dir="rtl">' + "".join(parts) + "</div>"


def main() -> None:
    t = load_json(TRANS)
    col_map = t["collections"]          # english title -> arabic title
    prod_t = t["products"]              # handle -> {title_ar, desc_ar}
    optname_map = t.get("option_names", {})
    optval_map = t.get("option_values", {})
    vendor_ar = t["brand"]["vendor_ar"]

    src_products = load_json(os.path.join(SRC, "catalog", "products.json"))
    src_by_handle = {p["handle"]: p for p in src_products}

    # collection -> product handles (from source collection files)
    src_col_dir = os.path.join(SRC, "collections")
    collections_of: dict[str, list[str]] = {}
    src_collections = []
    for f in sorted(os.listdir(src_col_dir)):
        c = load_json(os.path.join(src_col_dir, f))
        src_collections.append(c)
        for h in c["product_handles"]:
            collections_of.setdefault(h, []).append(c["title"])

    missing = [h for h in src_by_handle if h not in prod_t]
    if missing:
        print("WARNING: no Arabic translation for:", missing)

    ar_products = []
    index_rows = []

    for handle, src in sorted(src_by_handle.items()):
        tr = prod_t.get(handle, {})
        title_ar = tr.get("title_ar", src["title"])
        desc_ar = tr.get("desc_ar", "")
        cats_en = collections_of.get(handle, [])
        cats_ar = [col_map.get(c, c) for c in cats_en]

        # image paths -> reference source scrape (relative from this product dir)
        pdir = os.path.join(HERE, "products", handle)
        img_files = []
        src_img_dir = os.path.join(SRC, "products", handle, "images")
        if os.path.isdir(src_img_dir):
            for name in sorted(os.listdir(src_img_dir)):
                abs_src = os.path.join(src_img_dir, name)
                img_files.append({
                    "file": os.path.relpath(abs_src, pdir),
                    "src_url": None,
                })
        # keep original CDN urls too (useful for Salla bulk image import)
        for i, im in enumerate(src.get("images", [])):
            if i < len(img_files):
                img_files[i]["src_url"] = im.get("src")

        # localized variants (prices unchanged; option labels translated)
        variants_ar = []
        for v in src.get("variants", []):
            vv = dict(v)
            vv["title"] = optval_map.get(v.get("title"), v.get("title"))
            for key in ("option1", "option2", "option3"):
                if vv.get(key):
                    vv[key] = optval_map.get(vv[key], vv[key])
            variants_ar.append(vv)

        options_ar = []
        for o in src.get("options", []):
            options_ar.append({
                "name": optname_map.get(o.get("name"), o.get("name")),
                "values": [optval_map.get(x, x) for x in o.get("values", [])],
            })

        full = {
            "id": src.get("id"),
            "handle": handle,
            "title": title_ar,
            "title_en": src["title"],
            "vendor": vendor_ar,
            "product_type": src.get("product_type") or "",
            "categories": cats_ar,
            "categories_en": cats_en,
            "url": f"https://clasicowatches.com/products/{handle}",
            "description_text": desc_ar,
            "body_html": desc_to_html(desc_ar) if desc_ar else "",
            "options": options_ar,
            "variants": variants_ar,
            "images": img_files,
            "price_min": min((float(v["price"]) for v in src.get("variants", []) if v.get("price")), default=None),
            "language": "ar",
        }
        write_json(os.path.join(pdir, "product_ar.json"), full)
        _write_md(pdir, full)
        ar_products.append(full)

        cats = " / ".join(cats_ar)
        for v in variants_ar or [{}]:
            index_rows.append([
                handle, title_ar, src["title"], vendor_ar, cats,
                v.get("sku", ""), v.get("price", ""),
                v.get("compare_at_price", "") or "",
                len(img_files), full["url"],
            ])

    # ---- catalog-level outputs ----
    write_json(os.path.join(HERE, "catalog", "products_ar.json"), ar_products)

    ar_collections = []
    for c in src_collections:
        ar_collections.append({
            "handle": c["handle"],
            "title": col_map.get(c["title"], c["title"]),
            "title_en": c["title"],
            "products_count": len(c["product_handles"]),
            "product_handles": c["product_handles"],
        })
        write_json(os.path.join(HERE, "collections", f"{c['handle']}_ar.json"),
                   ar_collections[-1])
    write_json(os.path.join(HERE, "catalog", "collections_ar.json"), ar_collections)

    # by-collection index (Arabic)
    by_col: dict[str, list[str]] = {}
    for p in ar_products:
        for c in (p["categories"] or ["غير مصنّف"]):
            by_col.setdefault(c, []).append(p["title"])
    write_json(os.path.join(HERE, "indexes", "by_collection_ar.json"),
               {k: sorted(v) for k, v in sorted(by_col.items())})

    # CSV (utf-8-sig so Excel shows Arabic correctly)
    csv_path = os.path.join(HERE, "catalog", "products_index_ar.csv")
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["handle", "الاسم (عربي)", "الاسم الأصلي", "العلامة",
                    "التصنيفات", "SKU", "السعر", "السعر قبل الخصم",
                    "عدد الصور", "الرابط"])
        w.writerows(index_rows)

    print(f"Built Arabic catalog: {len(ar_products)} products, "
          f"{len(ar_collections)} collections")
    print(f"  -> {os.path.join(HERE, 'catalog')}")


def _write_md(pdir, full) -> None:
    lines = [f"# {full['title']}", ""]
    lines += [
        f"- **الاسم (عربي):** {full['title']}",
        f"- **الاسم الأصلي:** {full['title_en']}",
        f"- **العلامة:** {full['vendor']}",
        f"- **التصنيفات:** {'، '.join(full['categories']) or '-'}",
        f"- **السعر:** {full.get('price_min')} ",
        f"- **عدد الصور:** {len(full['images'])}",
        f"- **الرابط الأصلي:** {full['url']}",
        "",
        "## الوصف",
        "",
        full["description_text"] or "-",
    ]
    with open(os.path.join(pdir, "details_ar.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


if __name__ == "__main__":
    main()
