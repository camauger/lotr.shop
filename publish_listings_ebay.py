"""
Publie les annonces sur eBay via l'API Trading (AddItem).

Lit data/inventory.csv + listings générés (description HTML, images) et crée
une annonce par ligne pour le marketplace choisi. Enregistre les ItemID dans
data/ebay_listing_ids.json pour révision / relistage ultérieur.

Usage :
  python publish_listings_ebay.py [--marketplace ebay.ca] [--dry-run] [--limit N]

Prérequis : config/settings.yaml (ebay_api rempli), listings générés (images
uploadées si besoin), category_id listing correct pour le site.
"""

import argparse
import csv
import json
import time
from pathlib import Path
from typing import cast

import yaml

try:
    from ebaysdk.trading import Connection as Trading
except ImportError:
    Trading = None

CONFIG_PATH = Path("config/settings.yaml")
DATA_DIR = Path("data")
INVENTORY_CSV = DATA_DIR / "inventory.csv"
LISTING_IDS_FILE = DATA_DIR / "ebay_listing_ids.json"
PROCESSED_DIR = Path("processed")


def load_settings() -> dict:
    """Load YAML settings."""
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return cast(dict, yaml.safe_load(f))


def load_inventory(path: Path) -> list[dict]:
    """Load inventory CSV as list of dicts."""
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_listing_ids() -> dict[str, dict]:
    """Load SKU -> { item_id, marketplace } from previous runs."""
    if not LISTING_IDS_FILE.exists():
        return {}
    with open(LISTING_IDS_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_listing_ids(mapping: dict[str, dict]) -> None:
    """Save SKU -> { item_id, marketplace }."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(LISTING_IDS_FILE, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)


def load_image_urls(processed_dir: Path) -> dict[str, dict[str, str]]:
    """Load SKU -> { recto, verso } URLs from image_urls.json or image_urls_ebay.json."""
    for name in ("image_urls_ebay.json", "image_urls.json"):
        p = processed_dir / name
        if p.exists():
            with open(p, encoding="utf-8") as f:
                return json.load(f)
    return {}


def load_descriptions_for_marketplace(marketplace: str) -> dict[str, str]:
    """Load SKU -> DescriptionHTML from generated listings CSV if it exists."""
    slug = marketplace.replace(".", "_")
    csv_path = Path(f"listings_ebay_{slug}.csv")
    if not csv_path.exists():
        return {}
    out: dict[str, str] = {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sku = row.get("SKU", "")
            desc = row.get("DescriptionHTML", "")
            if sku and desc:
                out[sku] = desc
    return out


def build_add_item_payload(
    row: dict,
    description_html: str,
    picture_urls: list[str],
    category_id: str,
    condition_id: str,
    listing_duration: str,
    currency: str,
) -> dict:
    """Build AddItem request dict for Trading API."""
    title = row.get("Title", "")[:80]
    price = row.get("Price", "0")
    qty = row.get("Quantity", "1")
    sku = row.get("SKU", "")

    item: dict = {
        "Title": title,
        "Description": description_html,
        "PrimaryCategory": {"CategoryID": category_id},
        "StartPrice": str(price),
        "Currency": currency,
        "ListingType": "FixedPriceItem",
        "Quantity": str(max(1, int(float(qty) or 1))),
        "ConditionID": condition_id,
        "SKU": sku,
        "ListingDuration": listing_duration if listing_duration != "GTC" else "GTC",
        "DispatchTimeMax": "3",
    }
    if picture_urls:
        item["PictureDetails"] = {"PictureURL": picture_urls[:12]}
    return {"Item": item}


def get_trading_connection(settings: dict):
    """Return Trading API connection."""
    if Trading is None:
        raise RuntimeError("ebaysdk not installed: pip install ebaysdk")
    creds = settings.get("ebay_api", {})
    domain = (
        "api.sandbox.ebay.com"
        if creds.get("environment") == "sandbox"
        else "api.ebay.com"
    )
    return Trading(
        config_file=None,
        appid=creds.get("app_id"),
        devid=creds.get("dev_id"),
        certid=creds.get("cert_id"),
        token=creds.get("auth_token"),
        domain=domain,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish inventory listings to eBay")
    parser.add_argument(
        "--marketplace",
        default="ebay.ca",
        help="Marketplace (ebay.com, ebay.ca, ebay.fr)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not call API, only print payloads",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Max number of listings to publish (0 = all)",
    )
    args = parser.parse_args()

    settings = load_settings()
    if not INVENTORY_CSV.exists():
        print(f"Missing {INVENTORY_CSV}. Run generate_inventory.py first.")
        return

    marketplace = args.marketplace
    listing_cfg = settings.get("ebay_api", {}).get("listing", {})
    category_ids = listing_cfg.get("category_id", {})
    category_id = (
        category_ids.get(marketplace) or category_ids.get("ebay.com") or "2536"
    )
    condition_id = listing_cfg.get("condition_id", "1000")
    listing_duration = listing_cfg.get("duration", "GTC")
    currency = settings.get("currency", "CAD")
    processed_dir = Path(settings.get("paths", {}).get("processed", str(PROCESSED_DIR)))

    inventory = load_inventory(INVENTORY_CSV)
    descriptions = load_descriptions_for_marketplace(marketplace)
    image_urls = load_image_urls(processed_dir)
    listing_ids = load_listing_ids()

    if not descriptions:
        print(
            f"No descriptions for {marketplace}. Run build_listings.py first to create "
            f"listings_ebay_{marketplace.replace('.', '_')}.csv"
        )
        return

    to_publish = [r for r in inventory if r.get("SKU") in descriptions]
    if args.limit:
        to_publish = to_publish[: args.limit]

    print(
        f"Marketplace: {marketplace}, category: {category_id}, listings: {len(to_publish)}"
    )
    if args.dry_run:
        for row in to_publish[:3]:
            sku = row.get("SKU", "")
            desc = descriptions.get(sku, "")
            urls = image_urls.get(sku, {})
            pics = [urls.get("recto"), urls.get("verso")]
            pics = [u for u in pics if u]
            payload = build_add_item_payload(
                row, desc, pics, category_id, condition_id, listing_duration, currency
            )
            print(f"  [DRY-RUN] {sku} -> Title: {payload['Item']['Title'][:50]}...")
        print("  ... (dry-run, no API calls)")
        return

    api = get_trading_connection(settings)
    # SiteID for request (eBay US=0, Canada=2, France=71, etc.)
    site_map = {"ebay.com": "0", "ebay.ca": "2", "ebay.fr": "71"}
    site_id = site_map.get(marketplace, "0")

    for i, row in enumerate(to_publish):
        sku = row.get("SKU", "")
        desc = descriptions.get(sku, "")
        urls = image_urls.get(sku, {})
        pics = [urls.get("recto"), urls.get("verso")]
        pics = [u for u in pics if u]
        payload = build_add_item_payload(
            row, desc, pics, category_id, condition_id, listing_duration, currency
        )
        payload["Item"]["Site"] = site_id
        try:
            resp = api.execute("AddItem", payload)
            item_id = resp.reply.ItemID
            listing_ids[sku] = {"item_id": item_id, "marketplace": marketplace}
            print(f"  OK {sku} -> ItemID {item_id}")
        except Exception as e:
            print(f"  ERR {sku}: {e}")
        if i < len(to_publish) - 1:
            time.sleep(1)

    save_listing_ids(listing_ids)
    print(f"Done. Listing IDs saved to {LISTING_IDS_FILE}")


if __name__ == "__main__":
    main()
