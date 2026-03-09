"""
Recadre les images dans upload/ selon config/settings.yaml (images.crop).

- Si crop.margin > 0 : enlève N pixels de chaque cote (gauche, haut, droite, bas).
- Sinon si crop.width et crop.height > 0 : rectangle (left, top, width, height).

Usage : python crop_upload_images.py
"""

from pathlib import Path

import cv2
import yaml

CONFIG_PATH = Path("config/settings.yaml")
UPLOAD_DIR = Path("upload")
EXTENSIONS = {".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"}


def load_settings() -> dict:
    """Load YAML settings."""
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def crop_with_margin(img, margin: int):
    """Crop margin pixels from each side. Returns cropped image."""
    h, w = img.shape[:2]
    if margin <= 0 or 2 * margin >= min(w, h):
        return img
    return img[margin : h - margin, margin : w - margin].copy()


def crop_rect(img, left: int, top: int, width: int, height: int):
    """Crop to (left, top, width, height)."""
    h, w = img.shape[:2]
    x2 = min(left + width, w)
    y2 = min(top + height, h)
    return img[top:y2, left:x2].copy()


def main() -> None:
    if not CONFIG_PATH.exists():
        print(f"Erreur: {CONFIG_PATH} introuvable.")
        return
    if not UPLOAD_DIR.exists():
        print(f"Erreur: {UPLOAD_DIR} introuvable.")
        return

    settings = load_settings()
    crop_cfg = settings.get("images", {}).get("crop") or {}
    margin = int(crop_cfg.get("margin", 0))
    left = int(crop_cfg.get("left", 0))
    top = int(crop_cfg.get("top", 0))
    width = int(crop_cfg.get("width", 0))
    height = int(crop_cfg.get("height", 0))
    quality = int(settings.get("images", {}).get("jpeg_quality", 90))

    if margin > 0:
        print(f"Crop: marge {margin} px de chaque cote")
    elif width > 0 and height > 0:
        print(f"Crop: rect (left={left}, top={top}, width={width}, height={height})")
    else:
        print("Aucun crop configure (margin=0 et width/height=0). Rien a faire.")
        return

    count = 0
    for path in sorted(UPLOAD_DIR.iterdir()):
        if path.suffix not in EXTENSIONS:
            continue
        img = cv2.imread(str(path))
        if img is None:
            print(f"  SKIP (lecture impossible) {path.name}")
            continue
        if margin > 0:
            out = crop_with_margin(img, margin)
        else:
            out = crop_rect(img, left, top, width, height)
        if out.size == 0:
            print(f"  SKIP (crop invalide) {path.name}")
            continue
        cv2.imwrite(str(path), out, [cv2.IMWRITE_JPEG_QUALITY, quality])
        count += 1
        print(f"  OK {path.name}")

    print(f"OK {count} images recadrees.")


if __name__ == "__main__":
    main()
