# Pousser les listings sur eBay

Les CSV générés par `build_listings.py` contiennent titre, prix, description HTML et URLs d’images. Pour les transformer en annonces eBay, il faut passer par le **téléversement en masse** (Bulk upload) d’eBay, qui impose son propre modèle de fichier.

## Colonnes dans nos CSV

| Colonne        | Exemple / contenu                          |
|----------------|--------------------------------------------|
| SKU            | LOTR-01-1R284-NF-NM-01                     |
| Title          | Titre de l’annonce                          |
| Price          | Prix (ex. 2.5)                             |
| Currency       | CAD                                        |
| Marketplace    | ebay.com / ebay.ca / ebay.fr                |
| DescriptionHTML| Description complète (HTML)                 |
| PictureURL1    | URL recto (si upload_cdn ou upload_ebay)   |
| PictureURL2    | URL verso                                  |

Tu peux ouvrir `listings_ebay_ebay_com.csv` (ou _ebay_ca, _ebay_fr) dans Excel/LibreOffice pour copier ces champs dans le modèle eBay.

## Étapes sur eBay

1. **Seller Hub** → **Rapports** (Reports) → **Téléversements** (Uploads).
2. **Obtenir un modèle** (Get template) → **Créer de nouvelles annonces** (Create new listings).
3. Choisir la catégorie (ex. Cartes à collectionner > Jeu de cartes à collectionner > Le Seigneur des anneaux / Lord of the Rings TCG).
4. Télécharger le modèle (CSV ou Excel).
5. Remplir le modèle en copiant/collant depuis tes `listings_ebay_*.csv` :
   - Titre → colonne titre du modèle
   - Prix → colonne prix
   - Description HTML → colonne description (souvent « Description » ou « Item description »)
   - Images → colonnes image 1, image 2 du modèle (si tu as des URLs)
   - SKU → colonne SKU / Custom label si présente
6. Renseigner les **champs obligatoires** du modèle : condition, quantité, expédition, retours, etc. (souvent en référençant des **Business Policies** déjà créées dans ton compte).
7. Enregistrer le fichier, puis sur la page Téléversements : **Téléverser** le fichier. eBay vérifie et crée les annonces.

## Un CSV par site

- `listings_ebay_ebay_com.csv` → pour ebay.com
- `listings_ebay_ebay_ca.csv` → pour ebay.ca  
- `listings_ebay_ebay_fr.csv` → pour ebay.fr

Pour chaque site, télécharge le modèle correspondant au site cible et remplis-le avec le bon CSV.

## Liens utiles eBay

- [Téléverser des annonces en masse (Reports)](https://www.ebay.com/sh/reports/upload)
- [Aide : créer des annonces en masse](https://pages.ebay.com/sh/reports/help/create-listings-bulk/)
- [Modèles téléversables (Uploadable file feeds)](https://pages.ebay.com/sh/reports/help/uploadable-file-feeds/)

## Images vides dans le CSV

Si tu n’as pas exécuté `upload_cdn.py` ou `upload_ebay.py`, les colonnes PictureURL1 / PictureURL2 sont vides. Tu peux soit ajouter les URLs à la main dans le modèle eBay après upload des images sur eBay, soit exécuter un de ces scripts pour remplir les URLs automatiquement dans les prochains CSV.
