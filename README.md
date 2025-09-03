# LOTR TCG Shop – Setup & Run Guide

## Prérequis
- Python 3.10+
- pip
- Compte Cloudinary (optionnel, pour CDN)
- Identifiants eBay (optionnel, pour Picture Services)

## Installation
```bash
# Dans le dossier du projet
python -m venv .venv
# Git Bash (votre shell actuel)
source .venv/Scripts/activate
pip install -U pip setuptools wheel
pip install -r requirements.txt
```

- PowerShell (si vous basculez sur PS et voyez une erreur de scripts bloqués):
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```
- cmd.exe (Invite de commandes):
```bat
.venv\Scripts\activate.bat
```

## Configuration
Éditez `config/settings.yaml`:
- `currency: CAD`
- Marketplaces: `ebay.com` (par défaut), `ebay.ca`, `ebay.fr`
- Règles de langue: `ebay.fr` → fr, autres → en
- Images: `output_size_px: 1600`, `jpeg_quality: 90`
- Cloudinary: renseigner `cloud_name`, `api_key`, `api_secret` si utilisé
- eBay API: `environment`, `app_id`, `cert_id`, `dev_id`, `auth_token` si utilisé

## Structure des fichiers
- `input_raw/` photos brutes (recto/verso)
- `processed/` sorties normalisées + `manifest.json`
- `templates/description.html` modèle Jinja2
- `inventory.csv` inventaire source (en CAD)

## Convention de nommage images (SKU)
Format SKU: `LOTR-<SET>-<NUM>-<QUAL>` + suffixes fichiers
- Recto: `<SKU>_recto.jpg`
- Verso: `<SKU>_verso.jpg`
Exemple: `input_raw/LOTR-FOTR-123-NM-01_recto.jpg`

## Préparer l’inventaire
`inventory.csv` (en-têtes):
```
SKU,Title,Set,Number,Condition,Language,Price
```
Exemple:
```
LOTR-FOTR-123-NM-01,"Gandalf, The Grey",FOTR,123,NM,EN,9.99
```

## 1) Traitement des images
```bash
python process_images.py
```
- Lit `input_raw/`
- Écrit images normalisées dans `processed/` + `manifest.json`

## 2) Upload des images (au choix)
- CDN Cloudinary:
```bash
python upload_cdn.py
```
  - Produit `processed/image_urls.json`
- eBay Picture Services (sandbox/production selon config):
```bash
python upload_ebay.py
```
  - Produit `processed/image_urls_ebay.json`

## 3) Génération des listings eBay (CSV)
```bash
python build_listings.py
```
- Génère un CSV par marketplace: `listings_ebay_ebay_com.csv`, `listings_ebay_ebay_ca.csv`, `listings_ebay_ebay_fr.csv`
- Le CSV inclut les colonnes d’images `PictureURL1` (recto) et `PictureURL2` (verso) si `processed/image_urls.json` ou `processed/image_urls_ebay.json` existe.
- Règles:
  - eBay.fr → description en français
  - eBay.com / eBay.ca → description en anglais
  - Prix identiques en CAD sur tous les sites

## 4) Publication (voie rapide)
- Importez le CSV dans eBay Seller Hub (Bulk upload)

## Notes & astuces
- OpenCV: si problème d’installation Windows, réessayez avec `pip install --upgrade pip setuptools wheel`
- Cloudinary: nécessite des credentials valides, sinon l’upload échoue
- eBay SDK: privilégiez sandbox pour tests, puis passez en production

## Prochaines étapes
- Améliorer le cadrage (contours, homographie)
- Intégrer les URLs images dans le CSV eBay si nécessaire (déjà pris en charge)
- Ajouter relistage automatique via API eBay
