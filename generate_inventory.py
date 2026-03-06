"""
generate_inventory.py
Fusionne my_cards (Excel ou CSV) + master_cards.csv → inventory.csv complet

Usage :
    python generate_inventory.py

Prérequis :
    - data/master_cards.csv   (généré par build_master_db.py)
    - data/my_cards.xlsx ou data/my_cards.csv  (rempli à la main, Excel recommandé)
"""

import csv
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Chemins
# ---------------------------------------------------------------------------
DATA_DIR = Path("data")
MASTER = DATA_DIR / "master_cards.csv"
OUTPUT = DATA_DIR / "inventory.csv"
MY_CARDS_XLSX = DATA_DIR / "my_cards.xlsx"
MY_CARDS_CSV = DATA_DIR / "my_cards.csv"

# ---------------------------------------------------------------------------
# Colonnes finales dans inventory.csv
# ---------------------------------------------------------------------------
FIELDNAMES = [
    "SKU",
    "Title",
    "SetNum",
    "SetName",
    "CardID",
    "Rarity",
    "Kind",
    "Culture",
    "Twilight",
    "CardType",
    "GameText",
    "Condition",
    "Language",
    "Foil",
    "Foil/Regular",
    "Price",
    "Quantity",
]

CONDITION_VALID = {"NM", "LP", "MP", "HP", "D"}
LANGUAGE_VALID = {"EN", "FR", "DE", "IT", "ES", "PL"}


def normalize_card_id(card_id: str) -> str:
    """Retire le '+' optionnel (ex. 9R+49 → 9R49) pour la recherche dans master."""
    return card_id.replace("+", "")


# ---------------------------------------------------------------------------
# Générer le SKU
# ---------------------------------------------------------------------------
def is_foil(foil: str) -> bool:
    """True si la carte est foil (Y, YES, OUI, 1, TRUE)."""
    return foil.upper() in {"Y", "YES", "OUI", "1", "TRUE"}


def make_sku(
    set_num: str, card_id: str, foil: str, condition: str, language: str, idx: int = 1
) -> str:
    """
    Format : LOTR-<SetAbbr>-<CardID>[-F|-NF]-<Cond>[-<Lang>]-<idx:02d>
    Exemple : LOTR-02-2R1-NF-NM-01
              LOTR-02-2R1-F-LP-FR-01
    """
    parts = ["LOTR", f"{int(set_num):02d}", card_id]
    parts.append("F" if is_foil(foil) else "NF")
    parts.append(condition.upper())
    if language.upper() != "EN":
        parts.append(language.upper())
    parts.append(f"{idx:02d}")
    return "-".join(parts)


# ---------------------------------------------------------------------------
# Charger master_cards.csv → dict {CardID: row}
# ---------------------------------------------------------------------------
def load_master(path: Path) -> dict:
    """Load master_cards.csv into a dict keyed by CardID."""
    if not path.exists():
        raise FileNotFoundError(
            f"{path} introuvable — lance d'abord build_master_db.py"
        )
    master = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            master[row["CardID"]] = row
    print(f"✓ {len(master)} cartes dans master_cards.csv")
    return master


# ---------------------------------------------------------------------------
# Charger my_cards : Excel (.xlsx) ou CSV. Retourne liste de dict (clés = colonnes).
# ---------------------------------------------------------------------------
def _str(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    return str(val).strip()


def load_my_cards() -> tuple[list[dict], str]:
    """Retourne (liste d'entrées, chemin du fichier utilisé)."""
    if MY_CARDS_XLSX.exists():
        df = pd.read_excel(MY_CARDS_XLSX, sheet_name=0)
        df.columns = df.columns.str.strip()
        entries = []
        for _, row in df.iterrows():
            entries.append(
                {
                    "Set": _str(row.get("Set")),
                    "CardID": _str(row.get("CardID")),
                    "Condition": _str(row.get("Condition")),
                    "Language": _str(row.get("Language")),
                    "Foil": _str(row.get("Foil")),
                    "Price": _str(row.get("Price")),
                    "Quantity": _str(row.get("Quantity")),
                }
            )
        return entries, str(MY_CARDS_XLSX)
    if MY_CARDS_CSV.exists():
        with open(MY_CARDS_CSV, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f)), str(MY_CARDS_CSV)
    raise FileNotFoundError(
        f"Aucun fichier my_cards trouvé. Créez {MY_CARDS_XLSX} ou {MY_CARDS_CSV}"
    )


# ---------------------------------------------------------------------------
# Traitement principal
# ---------------------------------------------------------------------------
def generate(master: dict) -> list[dict]:
    """Merge my_cards with master and produce full inventory rows with SKUs."""
    rows = []
    sku_counter: dict[str, int] = {}
    errors = 0

    my_entries, my_path = load_my_cards()
    print(f"✓ {len(my_entries)} lignes lues depuis {my_path}")

    for line_num, entry in enumerate(my_entries, start=2):
        card_id_raw = entry.get("CardID", "").strip()
        card_id = normalize_card_id(card_id_raw)
        condition = entry.get("Condition", "NM").strip().upper()
        language = entry.get("Language", "EN").strip().upper()
        foil = entry.get("Foil", "N").strip() or "N"
        price = entry.get("Price", "").strip()
        qty_val = entry.get("Quantity", "1") or "1"
        quantity = int(float(qty_val)) if qty_val else 1

        # Validation basique (recherche avec CardID normalisé, ex. 9R+49 → 9R49)
        if card_id not in master:
            print(f"  ⚠ Ligne {line_num} : CardID '{card_id_raw}' inconnu dans master")
            errors += 1
            continue
        if condition not in CONDITION_VALID:
            print(
                f"  ⚠ Ligne {line_num} : Condition '{condition}' invalide "
                f"(valeurs : {CONDITION_VALID})"
            )
            errors += 1
            continue

        card = master[card_id]

        # Un exemplaire par ligne ; Quantity > 1 → plusieurs lignes avec idx croissant
        for _ in range(quantity):
            sku_key = f"{card_id}-{foil}-{condition}-{language}"
            sku_counter[sku_key] = sku_counter.get(sku_key, 0) + 1
            idx = sku_counter[sku_key]

            sku = make_sku(card["SetNum"], card_id, foil, condition, language, idx)

            rows.append(
                {
                    "SKU": sku,
                    "Title": card["Title"],
                    "SetNum": card["SetNum"],
                    "SetName": card["SetName"],
                    "CardID": card_id,
                    "Rarity": card["Rarity"],
                    "Kind": card["Kind"],
                    "Culture": card["Culture"],
                    "Twilight": card["Twilight"],
                    "CardType": card["CardType"],
                    "GameText": card["GameText"],
                    "Condition": condition,
                    "Language": language,
                    "Foil": foil.upper(),
                    "Foil/Regular": "Foil" if is_foil(foil) else "Regular",
                    "Price": price,
                    "Quantity": 1,
                }
            )

    print(f"✓ {len(rows)} entrées générées ({errors} erreurs)")
    return rows


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    """Load master and my_cards, generate inventory.csv."""
    master = load_master(MASTER)
    rows = generate(master)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✓ inventory.csv → {OUTPUT}  ({len(rows)} lignes)")


if __name__ == "__main__":
    main()
