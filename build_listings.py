import csv
import json
from pathlib import Path
from typing import Dict

import yaml
from jinja2 import Environment, FileSystemLoader


def load_settings(path: str = "config/settings.yaml") -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


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


def load_image_urls(processed_dir: str) -> Dict[str, Dict[str, str]]:
    cdn_path = Path(processed_dir) / "image_urls.json"
    ebay_path = Path(processed_dir) / "image_urls_ebay.json"
    mapping: Dict[str, Dict[str, str]] = {}
    if cdn_path.exists():
        with cdn_path.open("r", encoding="utf-8") as f:
            mapping = json.load(f)
    elif ebay_path.exists():
        with ebay_path.open("r", encoding="utf-8") as f:
            mapping = json.load(f)
    return mapping


def render_description(env: Environment, marketplace: str, row: Dict) -> str:
    template = env.get_template("description.html")
    return template.render(
        marketplace=marketplace,
        title=row.get("Title", ""),
        set=row.get("Set", ""),
        number=row.get("Number", ""),
        condition=row.get("Condition", ""),
        language=row.get("Language", ""),
        sku=row.get("SKU", ""),
    )


def build_csv(settings: Dict, marketplace: str) -> None:
    templates_dir = settings["paths"]["templates"]
    processed_dir = settings["paths"]["processed"]
    env = Environment(loader=FileSystemLoader(templates_dir))

    inventory_path = Path("inventory.csv")
    output_csv = Path(f"listings_ebay_{marketplace.replace('.', '_')}.csv")

    currency = settings.get("currency", "CAD")
    url_map = load_image_urls(processed_dir)

    with inventory_path.open("r", encoding="utf-8") as f_in, output_csv.open(
        "w", newline="", encoding="utf-8"
    ) as f_out:
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
