# Référence des scripts

Tous les scripts sont lancés à la racine du projet : `python script_name.py`.

---

## build_master_db.py

**Rôle** : Scraper wiki.lotrtcgpc.net pour construire la base de données des cartes.

**Entrée** : Aucune (lecture du wiki).

**Sortie** : `data/master_cards.csv` (CardID, SetNum, SetName, Rarity, Title, Kind, Culture, Twilight, CardType, GameText, WikiID, etc.).

**Usage** :
```bash
python build_master_db.py
```

- Long (environ 45 min pour ~3600 cartes) à cause du délai entre requêtes.
- **Reprise** : en cas d’interruption, relancer la commande ; les cartes déjà scrapées sont ignorées.
- Prend en charge les identifiants avec « + » (ex. 9R+49) et les enregistre normalisés (9R49).

**Dépendances** : `requests`, `beautifulsoup4`.

---

## generate_inventory.py

**Rôle** : Fusionner ton inventaire (Excel ou CSV) avec la base cartes et générer l’inventaire complet avec SKU.

**Entrée** :
- `data/master_cards.csv` (généré par build_master_db.py)
- `data/my_cards.xlsx` ou `data/my_cards.csv` (priorité au .xlsx)

**Sortie** : `data/inventory.csv` (SKU, Title, SetNum, SetName, CardID, Rarity, Kind, Culture, Twilight, CardType, GameText, Condition, Language, Foil, Foil/Regular, Price, Quantity).

**Usage** :
```bash
python generate_inventory.py
```

**Colonnes my_cards** : Set, CardID, Condition, Language, Foil, Price, Quantity. CardID doit exister dans le master ; les CardID avec « + » (ex. 9R+49) sont normalisés pour la recherche.

**Dépendances** : `pandas`, `openpyxl` (pour Excel).

---

## process_images.py

**Rôle** : Traiter les photos brutes (crop optionnel, redimensionnement, JPEG) et produire les images prêtes pour eBay.

**Entrée** :
- `config/settings.yaml` (paths, images.crop, images.output_size_px, jpeg_quality)
- `input_raw/<SKU>_recto.jpg`, `input_raw/<SKU>_verso.jpg`

**Sortie** :
- `processed/<SKU>_recto.jpg`, `processed/<SKU>_verso.jpg`
- `processed/manifest.json` (mapping SKU → chemins recto/verso)

**Usage** :
```bash
python process_images.py
```

**Dépendances** : OpenCV, PyYAML (voir `requirements.txt`).

---

## upload_cdn.py

**Rôle** : Envoyer les images de `processed/` vers Cloudinary et enregistrer les URLs.

**Entrée** : `config/settings.yaml` (paths.processed, cloudinary), fichiers `processed/*_recto.jpg`, `*_verso.jpg`.

**Sortie** : `processed/image_urls.json` (`{ "<SKU>": { "recto": "<url>", "verso": "<url>" } }`).

**Usage** :
```bash
python upload_cdn.py
```

**Dépendances** : `cloudinary`, PyYAML.

---

## upload_ebay.py

**Rôle** : Envoyer les images vers eBay Picture Services (API Trading).

**Entrée** : `config/settings.yaml` (paths.processed, ebay_api), fichiers dans `processed/`.

**Sortie** : `processed/image_urls_ebay.json` (même structure que image_urls.json).

**Usage** :
```bash
python upload_ebay.py
```

Utiliser `ebay_api.environment: sandbox` pour les tests. **Dépendances** : `ebaysdk`, PyYAML.

---

## build_listings.py

**Rôle** : Générer les CSV d’annonces eBay (titre, prix, description HTML, URLs images) par marketplace.

**Entrée** :
- `config/settings.yaml` (paths, currency, marketplaces)
- `data/inventory.csv`
- `templates/description.html`
- Optionnel : `processed/image_urls.json` ou `processed/image_urls_ebay.json`

**Sortie** : `listings_ebay_ebay_com.csv`, `listings_ebay_ebay_ca.csv`, `listings_ebay_ebay_fr.csv` (selon la config).

**Usage** :
```bash
python build_listings.py
```

Le template reçoit notamment : title, set, set_name, number, condition, language, rarity, kind, culture, twilight, card_type, game_text, foil, foil_y, sku. **Dépendances** : Jinja2, PyYAML.

---

## web/app.py (Streamlit — MVP site web)

**Rôle** : Afficher l’inventaire dans un site web avec recherche et filtres. MVP technique en vue d’une future synchro eBay (annonces, ventes, relistage).

**Entrée** :
- `config/settings.yaml` (paths.data pour le dossier des données)
- `data/inventory.csv` (généré par generate_inventory.py)

**Usage** (depuis la racine du projet) :
```bash
streamlit run web/app.py
```

Ouvre http://localhost:8501. Filtres : recherche (SKU, titre), set, condition, foil/regular, langue, fourchette de prix. **Vue cartes** : grille d’images (recto réel si présent dans `processed/`, sinon placeholder). Générer les placeholders avec `python generate_placeholders.py` pour afficher les cartes sans photo. **Dépendances** : `streamlit`, `polars`, PyYAML.

---

## generate_placeholders.py

**Rôle** : Générer les images placeholder (recto et verso) pour les cartes sans photo. Utilisées par le site web MVP et réutilisables ailleurs (ex. listings sans image).

**Entrée** : `config/settings.yaml` (images.output_size_px pour la taille).

**Sortie** : `static/placeholder_recto.jpg`, `static/placeholder_verso.jpg` (format carte TCG, couleurs LOTR).

**Usage** :
```bash
python generate_placeholders.py
```

À lancer une fois (ou après changement de `output_size_px`). **Dépendances** : Pillow, PyYAML.
