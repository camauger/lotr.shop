import json
import os
from pathlib import Path
from typing import Dict, List, Tuple

import cv2  # type: ignore
import numpy as np  # type: ignore
import yaml


def load_settings(settings_path: str = "config/settings.yaml") -> Dict:
    with open(settings_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def find_image_pairs(
    input_dir: str, recto_suffix: str, verso_suffix: str
) -> List[Tuple[str, str, str]]:
    pairs: List[Tuple[str, str, str]] = []
    for file in Path(input_dir).glob(f"*{recto_suffix}"):
        sku = file.name.replace(recto_suffix, "")
        verso = file.with_name(sku + verso_suffix)
        pairs.append((sku, str(file), str(verso)))
    return pairs


def auto_crop_and_normalize(img: np.ndarray, output_size: int) -> np.ndarray:
    # Placeholder: simple resize and center on white background
    h, w = img.shape[:2]
    scale = output_size / max(h, w)
    resized = cv2.resize(
        img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA
    )
    canvas = np.full((output_size, output_size, 3), 255, dtype=np.uint8)
    y_off = (output_size - resized.shape[0]) // 2
    x_off = (output_size - resized.shape[1]) // 2
    canvas[y_off : y_off + resized.shape[0], x_off : x_off + resized.shape[1]] = resized
    return canvas


def process_pair(
    recto_path: str, verso_path: str, settings: Dict
) -> Tuple[np.ndarray, np.ndarray]:
    img_recto = cv2.imread(recto_path)
    img_verso = cv2.imread(verso_path) if os.path.exists(verso_path) else None
    out_size = settings["images"]["output_size_px"]

    recto_out = auto_crop_and_normalize(img_recto, out_size)
    verso_out = (
        auto_crop_and_normalize(img_verso, out_size) if img_verso is not None else None
    )
    return recto_out, verso_out if verso_out is not None else recto_out


def save_jpeg(img: np.ndarray, out_path: str, quality: int) -> None:
    cv2.imwrite(out_path, img, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])


def main() -> None:
    settings = load_settings()
    input_dir = settings["paths"]["input_raw"]
    processed_dir = settings["paths"]["processed"]
    recto_suffix = settings["images"]["recto_suffix"]
    verso_suffix = settings["images"]["verso_suffix"]
    quality = settings["images"]["jpeg_quality"]

    Path(processed_dir).mkdir(parents=True, exist_ok=True)

    manifest: Dict[str, Dict[str, str]] = {}
    for sku, recto, verso in find_image_pairs(input_dir, recto_suffix, verso_suffix):
        recto_img, verso_img = process_pair(recto, verso, settings)
        recto_out = str(Path(processed_dir) / f"{sku}_recto.jpg")
        verso_out = str(Path(processed_dir) / f"{sku}_verso.jpg")
        save_jpeg(recto_img, recto_out, quality)
        save_jpeg(verso_img, verso_out, quality)
        manifest[sku] = {"recto": recto_out, "verso": verso_out}

    with open(Path(processed_dir) / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
