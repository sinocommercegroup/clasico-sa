# Clasico — Arabic Catalog (KSA / Salla)

Arabic-language product catalog for the **Clasico** watch brand, prepared for the
Saudi Salla store. 100% Arabic content — model & product names transliterated to
Arabic script, descriptions fully translated to MSA. Brand word "Clasico" is kept.

## Contents

| Path | What |
|---|---|
| `translations_ar.json` | Master editable map: all Arabic names + descriptions |
| `build_arabic.py` | Regenerates everything below from the map |
| `catalog/products_ar.json` | All 40 products (Arabic) |
| `catalog/collections_ar.json` | 11 collections (Arabic) |
| `catalog/products_index_ar.csv` | Flat sheet, Arabic headers (Excel-safe) |
| `products/<handle>/product_ar.json` | Per-product data + RTL `body_html` + image links |
| `products/<handle>/details_ar.md` | Readable Arabic product card |
| `collections/*_ar.json` | One file per collection |
| `indexes/by_collection_ar.json` | Products grouped by Arabic collection |

## Notes

- **Prices & SKUs** are unchanged from source.
- **Images** are not stored here (kept lean). Each product JSON keeps the original
  Shopify **CDN image URLs** (`images[].src_url`) — used for Salla bulk image import.
- To change any wording: edit `translations_ar.json`, then run `python3 build_arabic.py`.

## Purpose

Source of truth for uploading the Clasico catalog (products, categories, descriptions,
images) into the Salla store.
