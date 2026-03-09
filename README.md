# LOTR TCG Shop — Pipeline d'inventaire

Automatise la création des listings eBay pour une collection LOTR TCG.

## Documentation

- **Guides et référence** : le dossier [docs/](docs/) contient la documentation (guide pas à pas, architecture, configuration, référence des scripts). Tu peux la lire en Markdown ou générer un site avec MkDocs :
  ```bash
  pip install -r requirements-docs.txt
  mkdocs serve
  ```
  Puis ouvrir http://127.0.0.1:8000
- **AGENTS.md** : contexte pour les assistants IA. **ROADMAP.md** : objectifs et étapes du projet.

## Structure du projet

```
lotr-shop/
├── config/
│   └── settings.yaml          ← configuration centrale
├── data/
│   ├── master_cards.csv        ← base de données des cartes (générée)
│   ├── my_cards.xlsx           ← TON inventaire (Excel, recommandé)
│   ├── my_cards.csv            ← ou en CSV si tu préfères
│   └── inventory.csv           ← inventaire complet (généré)
├── input_raw/                  ← photos brutes (recto/verso par SKU)
├── processed/                  ← images traitées
├── upload/                     ← images prêtes pour eBay
├── static/                     ← placeholder recto/verso (générés, voir ci‑dessous)
├── web/
│   └── app.py                  ← site MVP (Streamlit) — inventaire + filtres
├── build_master_db.py          ← scraper wiki → master_cards.csv
├── generate_inventory.py       ← my_cards + master → inventory.csv
├── generate_placeholders.py    ← génère static/placeholder_recto.jpg et _verso.jpg
└── process_images.py           ← traitement photo (crop + resize)
```

## Installation

```bash
pip install -r requirements.txt
```

Pour lancer uniquement le **site web MVP** (inventaire + filtres) :

```bash
pip install -r requirements.txt
streamlit run web/app.py
```

Ouvre http://localhost:8501 — l’app lit `data/inventory.csv` (génère-le avant avec `python generate_inventory.py`). Filtres : recherche (SKU/titre), set, condition, foil/regular, langue, prix. La **vue cartes** affiche l’image de chaque carte si elle existe dans `processed/`, sinon une image placeholder. Pour générer les placeholders (une fois) : `python generate_placeholders.py` → crée `static/placeholder_recto.jpg` et `placeholder_verso.jpg`. Prochaine étape prévue : synchro eBay (annonces, ventes, relistage).

## Étape 1 — Construire la base de données

À faire **une seule fois** (ou pour mise à jour) :

```bash
python build_master_db.py
```

Scrape ~3600 cartes depuis wiki.lotrtcgpc.net (~45 min avec le délai poli).
Résultat : `data/master_cards.csv`

La commande est **resumable** : si elle est interrompue, relance-la,
elle reprend où elle s'est arrêtée.

## Étape 2 — Saisir ton inventaire

Tu peux utiliser **Excel** (plus pratique) ou CSV.

- **Excel :** crée ou édite `data/my_cards.xlsx` avec une feuille dont les en-têtes de colonnes sont exactement : `Set`, `CardID`, `Condition`, `Language`, `Foil`, `Price`, `Quantity`.
- **CSV :** édite `data/my_cards.csv`. Si `my_cards.xlsx` existe, il est utilisé en priorité.

Exemple (même structure en Excel ou CSV) :

```csv
Set,CardID,Condition,Language,Foil,Price,Quantity
2,2R1,NM,EN,N,2.50,1
1,1R1,LP,EN,N,1.00,2
```

| Colonne    | Valeurs acceptées                  | Exemple |
|------------|------------------------------------|---------|
| CardID     | SetRarityNum (ex. 2R1, 1C15)       | 2R1     |
| Condition  | NM / LP / MP / HP / D              | NM      |
| Language   | EN / FR / DE / IT / ES / PL        | EN      |
| Foil       | Y / N                              | N       |
| Price      | Nombre décimal en CAD              | 2.50    |
| Quantity   | Entier (crée N lignes dans l'inv.) | 1       |

Le champ `Set` est ignoré (CardID contient déjà le set).
Il est conservé pour faciliter la saisie visuelle.

## Étape 3 — Générer l'inventaire complet

```bash
python generate_inventory.py
```

Produit `data/inventory.csv` avec tous les champs enrichis + SKU générés (dont **Foil/Regular** : Foil ou Regular selon la carte).

**Format SKU :** `LOTR-<Set>-<CardID>-<Foil>-<Cond>[-<Lang>]-<idx>`
Exemple : `LOTR-02-2R1-NF-NM-01`

## Étape 4 — Photos

Nomme tes fichiers photo d'après le SKU :
```
input_raw/LOTR-02-2R1-NF-NM-01_recto.jpg
input_raw/LOTR-02-2R1-NF-NM-01_verso.jpg
```

```bash
python process_images.py
```

## Étape 5 — Texte des listings et CSV eBay

Le script **génère le texte de description** de chaque annonce (HTML) à partir du template `templates/description.html`, puis produit un CSV par marketplace prêt pour l’import eBay.

**Optionnel :** si tu as uploadé les images (Cloudinary ou eBay Picture Services), les URLs sont ajoutées aux listings. Sinon, les colonnes image restent vides et tu pourras les remplir côté eBay.

```bash
python build_listings.py
```

Résultat : `listings_ebay_ebay_com.csv`, `listings_ebay_ebay_ca.csv`, `listings_ebay_ebay_fr.csv` (titre, prix, **description HTML**, images si disponibles).  
Tu peux modifier `templates/description.html` pour adapter le texte (Set, CardID, Foil/Regular, condition, langue, expédition, etc.).

## Site web (MVP)

Un petit site Streamlit affiche l’inventaire avec recherche et filtres. À lancer **depuis la racine du projet** :

```bash
streamlit run web/app.py
```

Ouvre http://localhost:8501. L’app utilise `config/settings.yaml` pour le chemin des données (`paths.data`) et lit `data/inventory.csv`. Filtres : recherche (SKU, titre), set, condition, foil/regular, langue, fourchette de prix. Structure prête pour brancher plus tard la synchro eBay.

## Identifiants de Set (référence rapide)

| SetNum | Nom                     | Abrév. |
|--------|-------------------------|--------|
| 1      | The Fellowship of the Ring | FOTR |
| 2      | Mines of Moria          | MOM    |
| 3      | Realms of the Elf-Lords | ROEL   |
| 4      | The Two Towers          | TTT    |
| 5      | Battle of Helm's Deep   | BOHD   |
| 6      | Ents of Fangorn         | EOF    |
| 7      | The Return of the King  | ROTK   |
| 8      | Siege of Gondor         | SOG    |
| 9      | Reflections             | REF    |
| 10     | Mount Doom              | MD     |
| 11     | Shadows                 | SHA    |
| 12     | Black Rider             | BR     |
| 13     | Bloodlines              | BL     |
| 14     | Expanded Middle-earth   | EME    |
| 15     | The Hunters             | HUN    |
| 16     | The Wraith Collection   | WC     |
| 17     | Rise of Saruman         | ROS    |
| 18     | Treachery & Deceit      | TD     |
| 19     | Ages' End               | AE     |
