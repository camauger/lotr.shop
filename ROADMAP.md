# LOTR TCG SHOP

## Objectif

Mettre en place un système automatisé pour :

1. Photographier les cartes LOTR TCG.
2. Traiter et normaliser les images.
3. Générer des descriptions et listings cohérents.
4. Publier automatiquement les annonces sur eBay.
5. Gérer inventaire, prix et relistage.

---

## 1. Préparation

* [ ] **Inventaire initial**

  * Créer un fichier `inventory.csv` avec colonnes : `SKU, Title, Set, Number, Condition, Language, Price`.
  * Attribuer un **SKU unique** à chaque carte.
  * Format SKU recommandé : `LOTR-<SET>-<NUM>-<QUAL>`
    * Préfixe jeu : `LOTR` (Lord of the Rings)
    * Set/extension : abréviation standard (`FOTR`, `TTT`, `ROTK`, etc.)
    * Numéro de carte : numéro officiel (ex. `123`)
    * Qualificatif (optionnel, séparé par `-`, ordre recommandé : Foil/NonFoil, Condition, Langue)
      * Foil/NonFoil → `F` ou `NF`
      * Condition → `NM`, `LP`, etc.
      * Langue → `FR`, `EN`, etc.
    * Exemples
      * `LOTR-FOTR-123-NM` → carte #123 de Fellowship of the Ring, Near Mint
      * `LOTR-TTT-045-F-NM` → carte foil #45 de The Two Towers, Near Mint
      * `LOTR-ROTK-210-NF-LP-FR` → carte non-foil #210 de Return of the King, Light Play, en français
    * Bonus : numérotation interne pour exemplaires multiples (suffixe `-01`, `-02`, ...)
      * `LOTR-FOTR-123-NM-01`, `LOTR-FOTR-123-NM-02`
      * Fichiers bruts : `input_raw/LOTR-FOTR-123-NM-01_recto.jpg`, `input_raw/LOTR-FOTR-123-NM-01_verso.jpg`
      * Inventaire/annonce : `SKU = LOTR-FOTR-123-NM-01`
* [ ] **Organisation projet**

  * Définir arborescence (`input_raw/`, `processed/`, `upload/`, `templates/`).
  * Créer `config/settings.yaml` pour centraliser tailles, qualité JPEG, clés API.
  * Configurer la devise par défaut : CAD (dollars canadiens).
  * Définir les marketplaces cibles : eBay.com (par défaut), eBay.ca, eBay.fr.

---

## 2. Prise de vue

* [ ] **Setup matériel**

  * Lightbox, trépied, lampe LED, smartphone ou reflex.
  * Fond neutre (blanc/gris).
* [ ] **Workflow photo**

  * 1 photo recto + 1 verso par carte.
  * Ajouter **QR code SKU** ou dossier nommé par SKU.
* [ ] **Export brut** dans `input_raw/`.

---

## 3. Traitement d’images

* [ ] Développer script `process_images.py` pour :

  * Détection des contours (OpenCV).
  * Redressement (homographie).
  * Crop + normalisation taille (1600px, fond blanc).
  * Correction couleur (balance + contraste).
  * Export JPEG optimisé (sRGB, q=90).
  * Mapping image ↔ SKU (via QR/dossier).
* [ ] Générer `manifest.json` listant cartes ↔ images.

---

## 4. Génération des listings

* [ ] Créer `templates/description.html` (Jinja2) avec champs dynamiques : titre, set, condition, langue.
* [ ] Développer `build_listings.py` :

  * Lire `inventory.csv`.
  * Injecter infos dans template HTML.
  * Associer URLs des images (Cloudinary ou eBay Picture Service).
  * Produire `listings_ebay.csv` (format bulk import).
  * Règles de langue/prix :
    * eBay.fr → descriptions en français.
    * eBay.com / eBay.ca → descriptions en anglais.
    * Prix identiques en CAD sur tous les sites.

---

## 5. Upload des images

* **Option A (Cloudinary)**

  * [ ] Script `upload_cdn.py` pour envoyer images → CDN et récupérer URL.
* **Option B (eBay Picture Services)**

  * [ ] Script `upload_ebay.py` via `ebaysdk` pour héberger directement sur eBay.

---

## 6. Publication sur eBay

* [x] **Voie rapide** : Import CSV via *Seller Hub* (voir docs/ebay-upload.md).
* [x] **Publication via API** : `publish_listings_ebay.py` crée les annonces avec l’API Trading (AddItem). Prérequis : build_listings.py, images (upload_ebay.py), config ebay_api + listing.category_id. Les ItemID sont enregistrés dans data/ebay_listing_ids.json (voir docs/ebay-sync.md).
* [ ] **Ventes** : script pour récupérer les ventes (GetSellerTransactions / GetOrders) et mettre à jour l’inventaire ou un suivi ventes.
* [ ] **Relistage** : script pour relancer les annonces terminées (EndItem + AddItem ou ReviseItem) en s’appuyant sur ebay_listing_ids.json.
* [x] Paramètres marketplace : devise CAD ; sites cibles eBay.com, eBay.ca, eBay.fr.

---

## 7. Améliorations futures

* [ ] **Pricing dynamique** : comparer avec API “Finding” eBay pour ajuster automatiquement prix.
* [ ] **Analyse qualité** : détection de bordures abîmées, différenciation foil/non-foil.
* [x] **Dashboard MVP** (Streamlit) : `web/app.py` — affiche l’inventaire (`data/inventory.csv`) avec recherche et filtres (set, condition, foil, langue, prix). Lancer : `streamlit run web/app.py`. Structure prête pour brancher la synchro eBay plus tard.

---

## 8. Livrables finaux

* Scripts Python (`process_images.py`, `build_listings.py`, `upload_ebay.py`, etc.).
* Modèle `inventory.csv`.
* Template HTML description.
* Documentation `README.md` pour installation et exécution.
* Fichier `ROADMAP.md` (ce document).

---
