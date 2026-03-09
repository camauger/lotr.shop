"""
Génère les images placeholder (recto / verso) pour les cartes sans photo.

Utilise la taille de config/settings.yaml (images.output_size_px).
Sortie : static/placeholder_recto.jpg, static/placeholder_verso.jpg.

Usage : python generate_placeholders.py
"""
from __future__ import annotations

from pathlib import Path

import yaml

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as err:
    raise SystemExit("Pillow requis : pip install Pillow") from err

# Rapport largeur/hauteur carte TCG classique (2.5" x 3.5")
CARD_ASPECT = 2.5 / 3.5
CONFIG_PATH = Path("config/settings.yaml")
STATIC_DIR = Path("static")
PLACEHOLDER_RECTO = STATIC_DIR / "placeholder_recto.jpg"
PLACEHOLDER_VERSO = STATIC_DIR / "placeholder_verso.jpg"


def load_settings() -> dict:
    """Load YAML settings; return empty dict if file missing."""
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_output_size() -> int:
    """Return image output size (long edge) from config or default."""
    settings = load_settings()
    return int(
        settings.get("images", {}).get("output_size_px", 1600)
    )


def _get_fonts(size: int) -> tuple[ImageFont.FreeTypeFont | ImageFont.ImageFont, ...]:
    """Return (font_large, font_small); fallback to default if no TTF found."""
    candidates = [
        "arial.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            return (
                ImageFont.truetype(path, size=size),
                ImageFont.truetype(path, size=size // 2),
            )
        except OSError:
            continue
    default = ImageFont.load_default()
    return (default, default)


def make_placeholder(
    width: int,
    height: int,
    label: str,
    subtitle: str = "No image",
) -> Image.Image:
    """Draw a single placeholder image (LOTR-style colors, centered text)."""
    img = Image.new("RGB", (width, height), color=(44, 24, 16))  # dark brown
    draw = ImageDraw.Draw(img)

    # Border
    margin = max(width, height) // 80
    draw.rectangle(
        [(margin, margin), (width - margin, height - margin)],
        outline=(139, 90, 43),
        width=max(1, margin // 2),
    )

    size = min(width, height)
    font_large, font_small = _get_fonts(size // 12)

    def text_center(
        text: str,
        font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
        y_ratio: float,
    ) -> None:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        x = (width - tw) // 2
        y = int(height * y_ratio - th // 2)
        draw.text((x, y), text, fill=(218, 165, 32), font=font)

    text_center("LOTR TCG", font_large, 0.4)
    text_center(label, font_small, 0.52)
    text_center(subtitle, font_small, 0.62)

    return img


def main() -> None:
    """Generate recto and verso placeholder images in static/."""
    size_px = get_output_size()
    # Long edge = height (portrait)
    height = size_px
    width = int(height * CARD_ASPECT)

    STATIC_DIR.mkdir(parents=True, exist_ok=True)

    recto = make_placeholder(width, height, "Recto", "No image")
    recto.save(PLACEHOLDER_RECTO, "JPEG", quality=90)
    print(f"Written {PLACEHOLDER_RECTO} ({width}x{height})")

    verso = make_placeholder(width, height, "Verso", "No image")
    verso.save(PLACEHOLDER_VERSO, "JPEG", quality=90)
    print(f"Written {PLACEHOLDER_VERSO} ({width}x{height})")


if __name__ == "__main__":
    main()
