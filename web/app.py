"""
LOTR TCG Shop — MVP site web.

Affiche l'inventaire (data/inventory.csv) avec recherche et filtres.
Prépare le terrain pour une future synchro eBay.

Lancer : streamlit run web/app.py
"""

from pathlib import Path

import polars as pl
import streamlit as st
import yaml

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
CONFIG_PATH = Path("config/settings.yaml")
DEFAULT_DATA_DIR = Path("data")
INVENTORY_FILE = "inventory.csv"
STATIC_DIR = Path("static")
PLACEHOLDER_RECTO = STATIC_DIR / "placeholder_recto.jpg"
CARDS_PER_ROW = 4
MAX_CARDS_VIEW = 24


def load_settings() -> dict:
    """Load YAML settings; return empty dict if file missing."""
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_inventory_path() -> Path:
    """Return path to inventory.csv from config or default."""
    settings = load_settings()
    data_dir = settings.get("paths", {}).get("data", str(DEFAULT_DATA_DIR))
    return Path(data_dir) / INVENTORY_FILE


def get_processed_dir() -> Path:
    """Return path to processed images from config or default."""
    settings = load_settings()
    return Path(settings.get("paths", {}).get("processed", "processed"))


def get_card_image_path(sku: str, processed_dir: Path) -> Path:
    """Return path to card recto image if it exists, else placeholder."""
    recto = processed_dir / f"{sku}_recto.jpg"
    return recto if recto.exists() else PLACEHOLDER_RECTO


@st.cache_data
def load_inventory() -> pl.DataFrame:
    """Load inventory CSV; return empty DataFrame if missing."""
    path = get_inventory_path()
    if not path.exists():
        return pl.DataFrame()
    return pl.read_csv(path, encoding="utf-8")


def _unique_sorted(s: pl.Series) -> list[str]:
    """Return sorted unique non-null values as strings."""
    return sorted(str(x) for x in s.drop_nulls().unique().to_list())


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="LOTR TCG Shop — Inventaire",
    page_icon="🃏",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("LOTR TCG Shop — Inventaire")
st.caption("MVP site web · Données depuis data/inventory.csv")

df = load_inventory()
if df.is_empty():
    st.warning(
        f"Aucun inventaire trouvé. Génère-le avec : `python generate_inventory.py` "
        f"(fichier attendu : {get_inventory_path()})"
    )
    st.stop()

# Sidebar — Filtres
st.sidebar.header("Filtres")

search = st.sidebar.text_input("Recherche (SKU, titre)", "").strip()

col_set, col_cond = st.sidebar.columns(2)
with col_set:
    set_vals = ["Tous"] + _unique_sorted(df["SetName"])
    set_filter = st.selectbox("Set", set_vals)
with col_cond:
    cond_vals = ["Tous"] + _unique_sorted(df["Condition"])
    cond_filter = st.selectbox("Condition", cond_vals)

foil_vals = ["Tous"] + _unique_sorted(df["Foil/Regular"])
foil_filter = st.sidebar.selectbox("Foil / Regular", foil_vals)

lang_vals = ["Tous"] + _unique_sorted(df["Language"])
lang_filter = st.sidebar.selectbox("Langue", lang_vals)

price_col = "Price"
price_range: tuple[float, float] | None = None
if price_col in df.columns:
    try:
        price_series = df[price_col].cast(pl.Float64, strict=False)
        min_p = price_series.min()
        max_p = price_series.max()
        if min_p is not None and max_p is not None:
            min_p, max_p = float(min_p), float(max_p)
            price_range = st.sidebar.slider(
                "Prix (CAD)",
                min_value=min_p,
                max_value=max_p,
                value=(min_p, max_p),
                step=0.5,
            )
    except Exception:
        pass

# Appliquer filtres
pred = pl.lit(True)
if search:
    q = search
    pred = pred & (
        pl.col("SKU")
        .cast(pl.Utf8)
        .str.to_lowercase()
        .str.contains(q.lower(), literal=True)
        | pl.col("Title")
        .cast(pl.Utf8)
        .str.to_lowercase()
        .str.contains(q.lower(), literal=True)
    )
if set_filter != "Tous":
    pred = pred & (pl.col("SetName") == set_filter)
if cond_filter != "Tous":
    pred = pred & (pl.col("Condition") == cond_filter)
if foil_filter != "Tous":
    pred = pred & (pl.col("Foil/Regular") == foil_filter)
if lang_filter != "Tous":
    pred = pred & (pl.col("Language") == lang_filter)
if price_range is not None:
    p = pl.col(price_col).cast(pl.Float64, strict=False)
    pred = pred & (p >= price_range[0]) & (p <= price_range[1])

filtered = df.filter(pred)

# Stats
st.sidebar.divider()
st.sidebar.metric("Lignes affichées", len(filtered))
st.sidebar.metric("Total inventaire", len(df))

# Colonnes à afficher (éviter GameText trop long en vue table)
display_cols = [
    "SKU",
    "Title",
    "SetName",
    "CardID",
    "Rarity",
    "Condition",
    "Language",
    "Foil/Regular",
    "Price",
    "Quantity",
]
display_cols = [c for c in display_cols if c in filtered.columns]
table_df = filtered.select(display_cols) if display_cols else filtered

st.dataframe(
    table_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Price": st.column_config.NumberColumn(format="%.2f $"),
        "Quantity": st.column_config.NumberColumn(format="%d"),
    },
)

# Vue cartes : grille d'images (recto ou placeholder)
processed_dir = get_processed_dir()
show_df = filtered.head(MAX_CARDS_VIEW)
has_placeholder = PLACEHOLDER_RECTO.exists()
if not show_df.is_empty() and has_placeholder:
    st.subheader("Vue cartes")
    for start in range(0, len(show_df), CARDS_PER_ROW):
        chunk = show_df.slice(start, CARDS_PER_ROW)
        cols = st.columns(CARDS_PER_ROW)
        for i, row in enumerate(chunk.iter_rows(named=True)):
            with cols[i]:
                img_path = get_card_image_path(str(row["SKU"]), processed_dir)
                if img_path.exists():
                    st.image(str(img_path), use_container_width=True)
                title = str(row.get("Title", row["SKU"]))
                price = row.get("Price", "")
                st.caption(title[:43] + "…" if len(title) > 43 else title)
                if price != "":
                    st.caption(f"{price} $")

st.caption("Prochaine étape : synchro eBay (annonces, ventes, relistage).")
