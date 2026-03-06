# LOTR TCG Shop — Documentation

Pipeline d’inventaire et de listings eBay pour une collection **The Lord of the Rings Trading Card Game** (Decipher).

## Objectif

Automatiser la préparation des annonces eBay : base de données des cartes → saisie de ton inventaire → génération d’un inventaire enrichi avec SKU → traitement des photos → génération des descriptions et CSV prêts pour l’import eBay.

## Démarrage rapide

```bash
pip install -r requirements.txt
python build_master_db.py    # une fois (ou pour mise à jour)
# Éditer data/my_cards.xlsx
python generate_inventory.py
# Photos dans input_raw/<SKU>_recto.jpg, _verso.jpg
python process_images.py
python build_listings.py     # CSV eBay
```

## Documentation

| Page | Contenu |
|------|--------|
| [Guide pas à pas](guide.md) | Workflow complet : base de données → inventaire → photos → listings |
| [Architecture](architecture.md) | Flux de données, format SKU, rôles des fichiers |
| [Configuration](configuration.md) | `config/settings.yaml` (crop, chemins, marketplaces, API) |
| [Scripts](scripts.md) | Référence de chaque script Python |

## Fichiers du projet

- **README** (à la racine) — Instructions d’installation et d’utilisation (résumé opérationnel).
- **ROADMAP.md** — Objectifs et étapes du projet.
- **AGENTS.md** — Contexte pour les assistants IA (structure, conventions, tâches courantes).

**Qualité du code** : le projet utilise Ruff (lint/format) et mypy (types). Config dans `pyproject.toml`. Vérifier avant commit : `ruff check . && ruff format . && mypy .`
