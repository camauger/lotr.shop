"""
Renomme les images dans upload/ par ordre séquentiel selon data/inventory.csv.

Les noms IMG_2429, IMG_2430, ... sont remplacés par des slugs du titre
(produit 1 -> titre ligne 1, etc.) : ex. bilbo_retired_adventurer.jpeg

Usage (depuis la racine du projet) :
    python rename_upload_images.py
"""

import csv
import re
from pathlib import Path

DATA_DIR = Path("data")
UPLOAD_DIR = Path("upload")
INVENTORY_CSV = DATA_DIR / "inventory.csv"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"}


def slug(title: str, max_length: int = 80) -> str:
    """Convert title to a safe filename slug (lowercase, underscores)."""
    s = title.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = s.strip("_")
    return s[:max_length] if s else "unnamed"


def image_sort_key(path: Path) -> int:
    """Sort by numeric part of filename (IMG_2429 -> 2429)."""
    match = re.search(r"(\d+)", path.stem)
    return int(match.group(1)) if match else 0


def main() -> None:
    if not UPLOAD_DIR.exists():
        print(f"Erreur: {UPLOAD_DIR} introuvable.")
        return
    if not INVENTORY_CSV.exists():
        print(f"Erreur: {INVENTORY_CSV} introuvable. Lance generate_inventory.py.")
        return

    images = sorted(
        [p for p in UPLOAD_DIR.iterdir() if p.suffix in IMAGE_EXTENSIONS],
        key=image_sort_key,
    )
    if not images:
        print(f"Aucune image trouvee dans {UPLOAD_DIR}")
        return

    with open(INVENTORY_CSV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if len(rows) < len(images):
        print(
            f"Attention: {len(images)} images pour {len(rows)} produits. "
            f"Seules les {len(rows)} premieres images seront renommees."
        )

    used: dict[str, int] = {}
    ext_lower = images[0].suffix.lower()
    if ext_lower == ".jpeg":
        ext_lower = ".jpg"

    for i, img_path in enumerate(images):
        if i >= len(rows):
            break
        title = rows[i].get("Title", "").strip() or "unnamed"
        base = slug(title)
        if base in used:
            used[base] += 1
            new_name = f"{base}_{used[base]}{ext_lower}"
        else:
            used[base] = 1
            new_name = f"{base}{ext_lower}"

        new_path = img_path.parent / new_name
        if new_path == img_path:
            print(f"  (unchanged) {img_path.name}")
            continue
        if new_path.exists():
            print(f"  SKIP (exists) {img_path.name} -> {new_name}")
            continue
        img_path.rename(new_path)
        print(f"  {img_path.name} -> {new_name}")

    print(f"OK {min(len(images), len(rows))} images renommees.")


if __name__ == "__main__":
    main()
