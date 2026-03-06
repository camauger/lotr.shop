# Configuration

Toute la configuration centralisée se trouve dans **`config/settings.yaml`**.

## Devise et marketplaces

```yaml
currency: CAD

marketplaces:
  default: "ebay.com"
  additional:
    - "ebay.ca"
    - "ebay.fr"
  language_rules:
    ebay.com: en
    ebay.ca: en
    ebay.fr: fr
  pricing:
    identical_across_sites: true
```

- **currency** — Devise des prix (CAD).
- **marketplaces** — Sites eBay pour lesquels `build_listings.py` génère un CSV.
- **language_rules** — Langue des descriptions par site (fr pour ebay.fr, en pour les autres).
- **pricing** — Prix identiques en CAD sur tous les sites.

## Images (crop, taille, qualité)

```yaml
images:
  output_size_px: 1600
  jpeg_quality: 90
  color_space: sRGB
  background: white
  recto_suffix: "_recto.jpg"
  verso_suffix: "_verso.jpg"
  crop:
    left: 0
    top: 0
    width: 0
    height: 0
```

- **output_size_px** — Côté de l’image de sortie (carré).
- **jpeg_quality** — Qualité JPEG (1–100).
- **crop** — Zone de crop en pixels. Si `width` ou `height` vaut 0, aucun crop n’est appliqué. Sinon, la zone `(left, top, width, height)` est extraite avant redimensionnement.

Utilisé par : `process_images.py`.

## Chemins

```yaml
paths:
  input_raw: "input_raw"
  processed: "processed"
  data: "data"
  templates: "templates"
```

- **data** — Répertoire des CSV (master_cards, my_cards, inventory).
- **templates** — Répertoire du template Jinja2 (description eBay).

Utilisés par : `process_images.py`, `build_listings.py`, et les scripts d’upload selon le cas.

## Cloudinary (optionnel)

```yaml
cloudinary:
  enabled: true
  cloud_name: ""
  api_key: ""
  api_secret: ""
```

Renseigner les identifiants si tu utilises `upload_cdn.py`. Ne pas commiter de secrets (fichier local ou variables d’environnement).

## API eBay (optionnel)

```yaml
ebay_api:
  environment: sandbox  # ou production
  app_id: ""
  cert_id: ""
  dev_id: ""
  auth_token: ""
```

Utilisé par `upload_ebay.py`. En **sandbox** pour les tests, puis **production** pour les vrais listings.
