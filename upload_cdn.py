import json
from pathlib import Path
from typing import cast

import cloudinary
import cloudinary.uploader
import yaml


def load_settings(path: str = "config/settings.yaml") -> dict:
    """Load YAML settings from config file."""
    with open(path, encoding="utf-8") as f:
        return cast(dict, yaml.safe_load(f))


def configure_cloudinary(settings: dict) -> None:
    """Set Cloudinary config from settings (cloud_name, api_key, api_secret)."""
    creds = settings.get("cloudinary", {})
    cloudinary.config(
        cloud_name=creds.get("cloud_name", ""),
        api_key=creds.get("api_key", ""),
        api_secret=creds.get("api_secret", ""),
        secure=True,
    )


def upload_processed(processed_dir: str = "processed") -> dict[str, dict[str, str]]:
    """Upload processed recto/verso images to Cloudinary; return SKU -> {recto, verso} URLs."""
    mapping: dict[str, dict[str, str]] = {}
    for recto_file in Path(processed_dir).glob("*_recto.jpg"):
        sku = recto_file.name.replace("_recto.jpg", "")
        verso_file = recto_file.with_name(f"{sku}_verso.jpg")

        recto_resp = cloudinary.uploader.upload(
            str(recto_file), folder="lotr_tcg", public_id=f"{sku}_recto", overwrite=True
        )
        verso_resp = cloudinary.uploader.upload(
            str(verso_file), folder="lotr_tcg", public_id=f"{sku}_verso", overwrite=True
        )
        mapping[sku] = {
            "recto": recto_resp["secure_url"],
            "verso": verso_resp["secure_url"],
        }
    return mapping


def main() -> None:
    settings = load_settings()
    configure_cloudinary(settings)
    mapping = upload_processed(settings["paths"]["processed"])
    with open(
        Path(settings["paths"]["processed"]) / "image_urls.json", "w", encoding="utf-8"
    ) as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
