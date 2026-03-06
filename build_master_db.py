"""
build_master_db.py
Scrape wiki.lotrtcgpc.net → master_cards.csv

Champs extraits par carte :
  CardID, SetNum, SetName, Rarity, CardNumber, Title,
  Kind, Culture, Twilight, CardType, GameText
"""

import csv
import logging
import re
import time
from pathlib import Path
from urllib.parse import unquote, urljoin

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_URL = "https://wiki.lotrtcgpc.net"
OUTPUT = Path("data/master_cards.csv")
DELAY = 0.8  # secondes entre requêtes (respecte le serveur)
LOG_LEVEL = logging.INFO

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": "LOTRTCGShopBot/1.0 (personal collection tool; contact: you@email.com)"
    }
)

RARITY_MAP = {
    "C": "Common",
    "U": "Uncommon",
    "R": "Rare",
    "S": "Starter",
    "P": "Promo",
    "T": "Tournament",
    "X": "Fixed",
}

# ---------------------------------------------------------------------------
# Étape 1 : collecter toutes les URLs de cartes via Special:AllPages
# ---------------------------------------------------------------------------
# Match (9R49) ou (9R+49) — le + apparaît sur certaines cartes Reflections
CARD_PATTERN = re.compile(r"\(\d+[A-Z]+\d+\)$")
CARD_PATTERN_PLUS = re.compile(r"\(\d+[A-Z]+\+\d+\)$")


def collect_card_urls() -> list[str]:
    """Pagine Special:AllPages et retourne toutes les URLs de cartes."""
    urls: list[str] = []
    page_url: str | None = f"{BASE_URL}/wiki/Special:AllPages"

    while page_url:
        log.info("AllPages → %s", page_url)
        resp = SESSION.get(page_url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Liens de cartes dans le tableau principal
        body = soup.find("div", class_="mw-allpages-body")
        if body:
            for a in body.find_all("a", href=True):
                raw_href = a["href"]
                href_str = raw_href[0] if isinstance(raw_href, list) else raw_href
                if not href_str:
                    continue
                href_str = str(href_str)
                title = unquote(href_str.split("/wiki/")[-1])
                if CARD_PATTERN.search(title) or CARD_PATTERN_PLUS.search(title):
                    full = str(urljoin(BASE_URL, href_str))
                    if full not in urls:
                        urls.append(full)

        # Pagination : chercher le lien "Next page"
        nav = soup.find("div", class_="mw-allpages-nav")
        next_link = None
        if nav:
            for a in nav.find_all("a", href=True):
                if "Next" in a.get_text():
                    raw_next = a["href"]
                    next_href = raw_next[0] if isinstance(raw_next, list) else raw_next
                    next_link = str(urljoin(BASE_URL, str(next_href)))
                    break
        page_url = next_link
        time.sleep(DELAY)

    log.info("Total URLs collectées : %d", len(urls))
    return urls


# ---------------------------------------------------------------------------
# Étape 2 : parser une page de carte
# ---------------------------------------------------------------------------
def clean(text: str) -> str:
    """Supprime les espaces superflus."""
    return re.sub(r"\s+", " ", text).strip()


def parse_infobox_value(soup: BeautifulSoup, field_label: str) -> str:
    """
    Cherche la valeur d'un champ dans l'infobox de la carte.
    Les cellules suivent le pattern : <td>Label</td><td>Value</td>
    """
    for td in soup.find_all("td"):
        a = td.find("a")
        label = clean(a.get_text() if a else td.get_text())
        if label.lower() == field_label.lower():
            sibling = td.find_next_sibling("td")
            if sibling:
                return clean(sibling.get_text())
    return ""


def parse_card_page(url: str) -> dict | None:
    """Scrape une page de carte et retourne un dict de ses champs."""
    try:
        resp = SESSION.get(url, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        log.warning("Erreur réseau %s : %s", url, e)
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # Titre de la page = nom de la carte + identifiant ex. "Beneath the Mountains (2R1)"
    h1 = soup.find("h1", id="firstHeading")
    page_title = clean(h1.get_text()) if h1 else ""

    # Décomposer l'identifiant (2R1) ou (9R+49) → set, rarity, num (sans le +)
    card_id_match = re.search(r"\((\d+)([A-Z]+)\+?(\d+)\)$", page_title)
    if not card_id_match:
        log.debug("Pas d'identifiant de carte dans : %s", page_title)
        return None

    set_num = card_id_match.group(1)
    rarity_raw = card_id_match.group(2)
    card_num = card_id_match.group(3)
    card_id = f"{set_num}{rarity_raw}{card_num}"  # sans +, ex. 9R49
    title = page_title[: card_id_match.start()].strip()

    # Champs de l'infobox
    # Note : "Side" dans le wiki = Free Peoples / Shadow (= Kind dans le plan)
    set_name = parse_infobox_value(soup, "Set")
    kind = parse_infobox_value(soup, "Side")  # Free Peoples / Shadow
    culture = parse_infobox_value(soup, "Culture")
    twilight = parse_infobox_value(soup, "Twilight Cost")
    card_type = parse_infobox_value(soup, "Card Type")
    game_text = parse_infobox_value(soup, "Game Text")
    wiki_id = parse_infobox_value(soup, "Wiki Base Card ID")  # ex. LOTR-EN02S001.0

    rarity_label = RARITY_MAP.get(rarity_raw, rarity_raw)

    return {
        "CardID": card_id,
        "SetNum": set_num,
        "SetName": set_name,
        "Rarity": rarity_label,
        "RarityCode": rarity_raw,
        "CardNumber": card_num,
        "Title": title,
        "Kind": kind,
        "Culture": culture,
        "Twilight": twilight,
        "CardType": card_type,
        "GameText": game_text,
        "WikiID": wiki_id,
    }


# ---------------------------------------------------------------------------
# Étape 3 : écrire master_cards.csv avec reprise sur interruption
# ---------------------------------------------------------------------------
FIELDNAMES = [
    "CardID",
    "SetNum",
    "SetName",
    "Rarity",
    "RarityCode",
    "CardNumber",
    "Title",
    "Kind",
    "Culture",
    "Twilight",
    "CardType",
    "GameText",
    "WikiID",
]


def already_scraped(output: Path) -> set[str]:
    """Retourne les CardIDs déjà présents dans le CSV (reprise)."""
    if not output.exists():
        return set()
    with open(output, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return {row["CardID"] for row in reader}


def scrape_all(urls: list[str], output: Path) -> None:
    """Scrape each card URL and append rows to output CSV; skips already-scraped CardIDs."""
    done = already_scraped(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    mode = "a" if output.exists() else "w"
    with open(output, mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if mode == "w":
            writer.writeheader()

        for i, url in enumerate(urls, 1):
            # Extraire l'identifiant depuis l'URL pour vérifier la reprise (ex. 9R49 ou 9R+49)
            slug = unquote(url.split("/wiki/")[-1])
            id_match = re.search(r"\((\d+[A-Z]+\+?\d+)\)$", slug)
            if id_match:
                url_card_id = id_match.group(1).replace("+", "")
                if url_card_id in done:
                    log.debug("Déjà scrappé : %s", url_card_id)
                    continue

            log.info("[%d/%d] %s", i, len(urls), slug)
            card = parse_card_page(url)

            if card:
                writer.writerow(card)
                f.flush()
                done.add(card["CardID"])
            else:
                log.warning("Ignoré : %s", url)

            time.sleep(DELAY)

    log.info("master_cards.csv → %d cartes", len(done))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    log.info("=== build_master_db.py ===")
    card_urls = collect_card_urls()
    scrape_all(card_urls, OUTPUT)
    log.info("Terminé ✓")
