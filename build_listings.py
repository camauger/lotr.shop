import csv
import json
from pathlib import Path
from typing import cast

import yaml
from jinja2 import Environment, FileSystemLoader


def load_settings(path: str = "config/settings.yaml") -> dict:
    """Load YAML settings from config file."""
    with open(path, encoding="utf-8") as f:
        return cast(dict, yaml.safe_load(f))


essential_columns = [
    "SKU",
    "Title",
    "Price",
    "Currency",
    "Marketplace",
    "DescriptionHTML",
]

image_columns = [
    "PictureURL1",
    "PictureURL2",
]


def load_image_urls(processed_dir: str) -> dict[str, dict[str, str]]:
    """Load SKU -> {recto, verso} URL mapping from image_urls.json or image_urls_ebay.json."""
    cdn_path = Path(processed_dir) / "image_urls.json"
    ebay_path = Path(processed_dir) / "image_urls_ebay.json"
    mapping: dict[str, dict[str, str]] = {}
    if cdn_path.exists():
        with cdn_path.open("r", encoding="utf-8") as f:
            mapping = json.load(f)
    elif ebay_path.exists():
        with ebay_path.open("r", encoding="utf-8") as f:
            mapping = json.load(f)
    return mapping


def render_description(env: Environment, marketplace: str, row: dict) -> str:
    """Render listing description HTML from Jinja2 template and inventory row."""
    template = env.get_template("description.html")
    foil_label = row.get("Foil/Regular", "").strip() or (
        "Foil" if (row.get("Foil", "") or "").upper() == "Y" else "Regular"
    )
    return template.render(
        marketplace=marketplace,
        title=row.get("Title", ""),
        set=row.get("SetName", "") or row.get("Set", ""),
        set_name=row.get("SetName", "") or row.get("Set", ""),
        number=row.get("CardID", "") or row.get("Number", ""),
        condition=row.get("Condition", ""),
        language=row.get("Language", ""),
        rarity=row.get("Rarity", ""),
        kind=row.get("Kind", ""),
        culture=row.get("Culture", ""),
        twilight=row.get("Twilight", ""),
        card_type=row.get("CardType", ""),
        game_text=row.get("GameText", ""),
        lore=row.get("Lore", ""),
        foil=foil_label,
        foil_y=(foil_label == "Foil" or (row.get("Foil", "") or "").upper() == "Y"),
        sku=row.get("SKU", ""),
    )


def build_csv(settings: dict, marketplace: str) -> None:
    """Generate one eBay listings CSV for the given marketplace."""
    templates_dir = settings["paths"]["templates"]
    processed_dir = settings["paths"]["processed"]
    env = Environment(loader=FileSystemLoader(templates_dir))

    data_dir = Path(settings["paths"].get("data", "data"))
    inventory_path = data_dir / "inventory.csv"
    output_csv = Path(f"listings_ebay_{marketplace.replace('.', '_')}.csv")

    currency = settings.get("currency", "CAD")
    url_map = load_image_urls(processed_dir)

    with (
        inventory_path.open("r", encoding="utf-8") as f_in,
        output_csv.open("w", newline="", encoding="utf-8") as f_out,
    ):
        reader = csv.DictReader(f_in)
        fieldnames = essential_columns + image_columns
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            sku = row.get("SKU", "")
            desc = render_description(env, marketplace, row)
            urls = url_map.get(sku, {})
            picture1 = urls.get("recto", "")
            picture2 = urls.get("verso", "")

            writer.writerow(
                {
                    "SKU": sku,
                    "Title": row.get("Title", ""),
                    "Price": row.get("Price", ""),
                    "Currency": currency,
                    "Marketplace": marketplace,
                    "DescriptionHTML": desc,
                    "PictureURL1": picture1,
                    "PictureURL2": picture2,
                }
            )


def main() -> None:
    settings = load_settings()
    markets = [settings["marketplaces"]["default"]] + settings["marketplaces"].get(
        "additional", []
    )
    for m in markets:
        build_csv(settings, m)


if __name__ == "__main__":
    main()
