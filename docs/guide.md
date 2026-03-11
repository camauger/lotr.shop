# Guide pas à pas

Workflow complet pour préparer tes listings eBay à partir de ta collection LOTR TCG.

## Prérequis

- Python 3.10+
- Dépendances : `pip install -r requirements.txt` (voir README à la racine pour les commandes détaillées)

## 1. Construire la base de données des cartes

À faire **une seule fois** (ou pour mettre à jour le master) :

```bash
python build_master_db.py
```

- Scrape environ 3600 cartes depuis wiki.lotrtcgpc.net (durée ~45 min avec délai poli).
- Résultat : `data/master_cards.csv`.
- **Reprise** : en cas d’arrêt, relancer la commande ; elle reprend où elle s’est arrêtée.

## 2. Saisir ton inventaire

- **Excel (recommandé)** : crée ou édite `data/my_cards.xlsx` avec une feuille dont les en-têtes sont exactement :  
  `Set`, `CardID`, `Condition`, `Language`, `Foil`, `Price`, `Quantity`.
- **CSV** : édite `data/my_cards.csv` (même colonnes). Si `my_cards.xlsx` existe, il est utilisé en priorité.

Valeurs typiques : CardID (ex. 2R1, 9R49), Condition (NM, LP, MP, HP, D), Language (EN, FR, …), Foil (Y/N), Price en CAD, Quantity (entier).

Voir le README à la racine du projet pour le tableau des colonnes et exemples.

## 3. Générer l’inventaire complet

```bash
python generate_inventory.py
```

- Produit `data/inventory.csv` avec tous les champs enrichis (titre, set, rareté, type, texte de jeu, etc.) et les SKU générés.
- Format SKU : `LOTR-<Set>-<CardID>-<Foil>-<Cond>[-<Lang>]-<idx>` (ex. `LOTR-09-9R49-F-NM-01`).

## 4. Photos

- Place tes photos dans `input_raw/` en les nommant par SKU :
  - `input_raw/<SKU>_recto.jpg`
  - `input_raw/<SKU>_verso.jpg`
- Ajuste éventuellement le crop dans `config/settings.yaml` (section `images.crop`).
- Lance le traitement :

```bash
python process_images.py
```

Les images normalisées sont dans `processed/` et le mapping dans `processed/manifest.json`.

## 5. Listings eBay (texte + CSV)

- Le **texte de description** de chaque annonce est généré à partir de `templates/description.html` (Jinja2).
- **Optionnel** : upload des images pour obtenir les URLs dans les listings :
  - `python upload_cdn.py` (Cloudinary) ou `python upload_ebay.py` (eBay Picture Services).
- Génération des CSV par marketplace :

```bash
python build_listings.py
```

Résultat : `listings_ebay_ebay_com.csv`, `listings_ebay_ebay_ca.csv`, `listings_ebay_ebay_fr.csv`. Pour **pousser ces listings sur eBay**, utilise le téléversement en masse (Bulk upload) : Seller Hub → Rapports → Téléversements → Obtenir un modèle (Créer de nouvelles annonces), remplir le modèle avec les données de tes CSV, puis téléverser. Détail : [Pousser les listings sur eBay](ebay-upload.md). Pour personnaliser le texte, modifie `templates/description.html`.

## Référence rapide des sets

Voir le tableau « Identifiants de Set » dans le README à la racine du projet.
