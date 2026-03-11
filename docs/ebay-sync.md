# Synchro eBay (annonces, ventes, relistage)

Ce document décrit la synchro avec eBay : publication des annonces via API, suivi des ventes, relistage.

## 1. Publication des annonces (en place)

Le script **`publish_listings_ebay.py`** crée des annonces sur eBay à partir de l’inventaire et des listings générés (Trading API AddItem).

### Prérequis

- **config/settings.yaml** : section `ebay_api` remplie (app_id, cert_id, dev_id, auth_token), et `ebay_api.listing` (category_id par site, duration, condition_id).
- **Listings générés** : `python build_listings.py` pour produire les CSV (titres, descriptions HTML).
- **Images** : soit `upload_cdn.py` puis URLs dans les listings, soit `upload_ebay.py` pour héberger les images sur eBay (recommandé pour AddItem).
- **Category ID** : feuille de catégorie eBay pour « Trading Card Games > Lord of the Rings » (ou équivalent). Vérifier avec GetCategories ou le site eBay ; ex. 2536 pour ebay.com. Configurer par marketplace dans `ebay_api.listing.category_id`.

### Utilisation

```bash
# Publier sur ebay.ca (défaut)
python publish_listings_ebay.py

# Autre marketplace
python publish_listings_ebay.py --marketplace ebay.com

# Test sans appel API
python publish_listings_ebay.py --dry-run

# Limiter le nombre d’annonces
python publish_listings_ebay.py --limit 5
```

Les **ItemID** eBay sont enregistrés dans **`data/ebay_listing_ids.json`** (SKU → item_id, marketplace) pour révision et relistage ultérieurs.

### Sandbox vs production

- `ebay_api.environment: sandbox` → appels vers api.sandbox.ebay.com (tests).
- `ebay_api.environment: production` → api.ebay.com (annonces réelles).

---

## 2. Ventes (prévu)

- Récupérer les ventes : **Trading API** GetSellerTransactions / GetOrders (ou **Sell Fulfillment** Orders).
- Mettre à jour l’inventaire local (diminuer Quantity pour le SKU vendu) ou marquer les lignes vendues.
- Option : script `sync_sales_ebay.py` qui lit les commandes récentes et met à jour `data/inventory.csv` ou un fichier `data/sales.json`.

---

## 3. Relistage (prévu)

- Pour les annonces terminées sans vente : **Trading API** EndItem (si besoin) puis recréer avec AddItem, ou **ReviseItem** pour modifier et relancer.
- Utiliser `data/ebay_listing_ids.json` pour savoir quel ItemID correspond à quel SKU.
- Option : script `relist_ebay.py` qui liste les annonces terminées (GetMyeBaySelling), puis pour chaque SKU relance AddItem (ou ReviseItem) avec les mêmes données.

---

## Fichiers liés

| Fichier | Rôle |
|--------|------|
| **config/settings.yaml** | ebay_api (credentials, listing.category_id, duration, condition_id) |
| **data/inventory.csv** | Source des annonces (SKU, Title, Price, Quantity, etc.) |
| **data/ebay_listing_ids.json** | SKU → { item_id, marketplace } après publication |
| **listings_ebay_*.csv** | Descriptions HTML et infos par marketplace (générés par build_listings.py) |
| **processed/image_urls_ebay.json** | URLs des images hébergées sur eBay (après upload_ebay.py) |

---

## Évolutions possibles

- **Sell Inventory API** (REST, OAuth 2) : création d’offres via createOrReplaceInventoryItem, createOffer, publishOffer ; plus adapté à un gros volume et à la gestion d’inventaire multi-site. Nécessite une migration des credentials (OAuth) et des appels.
- **Feed API** : import en masse via fichiers pour créer/mettre à jour des annonces sans appeler AddItem une par une.
