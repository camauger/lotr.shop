# AGENTS.md

## Project Overview

**LOTR TCG Shop** is a Python automation pipeline for LOTR TCG card inventory and eBay listings. Main flow: build a master card database from the wiki → enter your cards in `my_cards.csv` → generate full inventory with SKUs → process photos by SKU. Goal: produce eBay-ready listings (CSV bulk upload). Optional steps: upload images to Cloudinary or eBay Picture Services, then run `build_listings.py` to generate per-marketplace CSVs.

Tech stack: Python 3.10+, `requests`, `beautifulsoup4` (wiki scraper), OpenCV, Pillow, PyYAML, Jinja2; optionally Cloudinary SDK, ebaysdk for listing generation. Configuration in `config/settings.yaml`; script-based workflow, no framework.

## Architecture

```
lotrtcg.shop/
├── config/
│   └── settings.yaml          # Configuration centrale (crop, paths, marketplaces, API)
├── data/
│   ├── master_cards.csv       # Base cartes (générée par build_master_db.py)
│   ├── my_cards.csv           # Ton inventaire saisi (Set, CardID, Condition, Language, Foil, Price, Quantity)
│   └── inventory.csv         # Inventaire complet généré (SKU + champs enrichis)
├── input_raw/                 # Photos brutes (recto/verso par SKU)
├── processed/                 # Images traitées + manifest.json
├── upload/                    # Images prêtes pour eBay
├── build_master_db.py         # Scraper wiki → master_cards.csv (resumable)
├── generate_inventory.py      # my_cards + master → inventory.csv
├── process_images.py          # Traitement photo (crop + resize) → processed/
├── templates/
│   └── description.html       # Template Jinja2 pour descriptions eBay (optionnel)
├── upload_cdn.py              # (optionnel) Upload Cloudinary → image_urls.json
├── upload_ebay.py             # (optionnel) Upload eBay Picture Services → image_urls_ebay.json
├── build_listings.py          # (optionnel) inventory + template + URLs → listings_ebay_<site>.csv
├── README.md
└── ROADMAP.md
```

**Data flow:** Wiki → `build_master_db.py` → `data/master_cards.csv`. You edit `data/my_cards.csv`; `generate_inventory.py` merges with master → `data/inventory.csv` (enriched + SKUs). Photos: `input_raw/` (named by SKU) → `process_images.py` → `processed/`. For eBay CSV listings, `upload_cdn.py` or `upload_ebay.py` then `build_listings.py` remain available to produce `listings_ebay_*.csv`.

## Coding Conventions

**Style**
- Use `pathlib.Path` for file paths; avoid raw `os.path` for new code.
- All file I/O: `encoding="utf-8"` for text.
- Type hints on function signatures and key variables (`Dict`, `List`, `Tuple` from `typing`).

**Naming**
- SKU format: `LOTR-<Set>-<CardID>-<Foil>-<Cond>[-<Lang>]-<idx>` (e.g. `LOTR-02-2R1-NF-NM-01`). Set is 2-digit; Foil is F or NF; CardID like 2R1, 1C15. Image filenames: `<SKU>_recto.jpg`, `<SKU>_verso.jpg`.
- Config keys and paths are defined in `config/settings.yaml`; scripts load via a `load_settings(path="config/settings.yaml")` helper where applicable.

**Patterns**
- Each script is runnable with `python script_name.py` and has a `main()` entrypoint.
- Settings: always read from YAML; do not hardcode paths or API keys in scripts.
- Prefer `Path(...).open(..., encoding="utf-8")` or `open(..., encoding="utf-8")` for JSON/CSV/HTML.

## Key Files

| File | Purpose |
|------|---------|
| `config/settings.yaml` | Crop (left/top/width/height), paths, image size/quality, marketplaces, language rules, API config |
| `build_master_db.py` | Scrapes wiki.lotrtcgpc.net → `data/master_cards.csv` (resumable) |
| `generate_inventory.py` | Merges my_cards + master → `data/inventory.csv` (SKU + enriched fields) |
| `data/master_cards.csv` | Card database: CardID, Title, SetNum, SetName, Rarity, Kind, Culture, etc. |
| `data/my_cards.csv` | Your input inventory: Set, CardID, Condition, Language, Foil, Price, Quantity |
| `data/inventory.csv` | **Generated** by `generate_inventory.py`. Columns: SKU, Title, SetNum, SetName, CardID, Condition, Language, Foil, Foil/Regular, Price, Quantity, plus Rarity, Kind, Culture, etc. |
| `process_images.py` | Finds recto/verso pairs in `input_raw/`, normalizes (crop/resize/JPEG), writes `processed/` + `manifest.json` |
| `upload_cdn.py` | (Listing eBay) Uploads processed images to Cloudinary → `processed/image_urls.json` |
| `upload_ebay.py` | (Listing eBay) Uploads via eBay Trading API → `processed/image_urls_ebay.json` |
| `build_listings.py` | (Listing eBay) Renders Jinja2 descriptions, merges image URLs, outputs one CSV per marketplace |
| `templates/description.html` | (Listing eBay) Description template (title, set, number, condition, language, sku, marketplace) |

## Development

**Setup**
```bash
pip install requests beautifulsoup4 pillow pyyaml
```
For image processing add OpenCV: `pip install opencv-python`. For full pipeline including eBay listing generation, `requirements.txt` may list opencv, jinja2, cloudinary, ebaysdk, etc. Edit `config/settings.yaml` for currency (CAD), marketplaces, image size/quality, and API credentials when using upload/build_listings.

**Test**
- No automated test suite yet. Validate by running the pipeline: `process_images.py` → `upload_cdn.py` or `upload_ebay.py` → `build_listings.py`, then inspect `processed/` and generated CSVs.

**Lint**
- No ruff/mypy config in repo; code uses type hints and consistent style. If adding tools later, keep line length and import style consistent with existing files.

## Common Tasks

**Update the card database**
1. Run `python build_master_db.py`. It is resumable: if interrupted, run again to continue from where it left off.
2. Result: `data/master_cards.csv` updated.

**Add cards to inventory**
1. Edit `data/my_cards.csv` (Set, CardID, Condition, Language, Foil, Price, Quantity).
2. Run `python generate_inventory.py` to regenerate `data/inventory.csv`.

**Add a new marketplace**
1. Add the site (e.g. `ebay.de`) under `config/settings.yaml` → `marketplaces.additional` and `marketplaces.language_rules`.
2. In `build_listings.py`, ensure the loop over marketplaces includes the new site and that `render_description` receives the correct language.

**Change image size or quality**
1. Edit `config/settings.yaml` → `images.output_size_px` and `images.jpeg_quality`.
2. Re-run `process_images.py` to regenerate `processed/` images and manifest.

**Add a field to listings CSV**
1. Extend `essential_columns` or add new columns in `build_listings.py`.
2. Populate from `inventory.csv` (add column there) or from settings; write in the `DictWriter` row.

**Fix or extend description template**
1. Edit `templates/description.html` (Jinja2). Variables passed: `marketplace`, `title`, `set`, `number`, `condition`, `language`, `sku`.
2. Re-run `build_listings.py` only; no need to re-process images.

## Constraints and Gotchas

- **generate_inventory.py** requires `data/master_cards.csv` and `data/my_cards.csv` to exist; every CardID in my_cards must be present in master.
- **eBay sandbox vs production:** Controlled by `config/settings.yaml` → `ebay_api.environment`. Use sandbox for tests; switch to production only when credentials and flow are validated.
- **Image URL source:** `build_listings.py` uses `image_urls.json` (Cloudinary) if present, else `image_urls_ebay.json`. Do not commit `config/settings.yaml` with real API keys; keep secrets out of version control (use env or local override).
- **OpenCV on Windows:** If `pip install opencv-python` fails, try `pip install --upgrade pip setuptools wheel` then reinstall.
- **Pricing:** All prices in inventory are in CAD; listings keep identical CAD pricing across eBay.com, eBay.ca, eBay.fr as per settings.

## AI Assistant Guidelines

- Prefer changing behavior via `config/settings.yaml` and template/data files rather than hardcoding in scripts.
- When adding dependencies, add them to `requirements.txt` with version bounds consistent with existing entries (e.g. `package>=x.y,<z`).
- Do not break `generate_inventory.py` output: preserve FIELDNAMES and the contract of generated `data/inventory.csv`. Do not remove or rename `manifest.json`, `image_urls.json`, or `image_urls_ebay.json` contract (keys = SKUs, values = `{"recto": url, "verso": url}`) used by build_listings.
- For new scripts, keep the same pattern: `load_settings()` where applicable, `Path`-based I/O, UTF-8, and `if __name__ == "__main__": main()`.
- Preserve backward compatibility for CSV column names and SKU/image naming so existing inventory and Seller Hub workflows keep working.
