from __future__ import annotations
import math
from html import escape

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine

# ====================== CONFIG ======================
st.set_page_config(page_title="Car Inventory", page_icon="🚗", layout="wide")

# Use your Neon connection string here:
# Example: "postgresql://user:pass@host/dbname?sslmode=require&channel_binding=require"
DB_URL = "postgresql://neondb_owner:npg_oaL4zTcPq7vI@ep-bitter-meadow-ag6jeaxp-pooler.c-2.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

ALL_COLUMNS = [
    "StockNo","Make","Model","Year","Trim","BodyStyle","Transmission","Fuel","Engine","Drivetrain",
    "Mileage","ExteriorColor","InteriorColor","VIN","Price","Condition","Features","Location","Photo"
]

TEXT_COLS = [
    "StockNo","Make","Model","Trim","BodyStyle","Transmission","Fuel","Engine","Drivetrain",
    "ExteriorColor","InteriorColor","VIN","Condition","Features","Location","Photo"
]
NUM_COLS = ["Year","Mileage","Price"]

# ====================== HELPERS ======================
@st.cache_data
def load_db(db_url: str) -> pd.DataFrame:
    engine = create_engine(db_url)

    with engine.connect() as conn:
        # Assume Postgres stored everything in lowercase: store, stockno, make, etc.
        # We alias them back to the camel-case column names your app expects.
        df = pd.read_sql(
            """
            SELECT
                stockno        AS "StockNo",
                make           AS "Make",
                model          AS "Model",
                year           AS "Year",
                trim           AS "Trim",
                bodystyle      AS "BodyStyle",
                transmission   AS "Transmission",
                fuel           AS "Fuel",
                engine         AS "Engine",
                drivetrain     AS "Drivetrain",
                mileage        AS "Mileage",
                exteriorcolor  AS "ExteriorColor",
                interiorcolor  AS "InteriorColor",
                vin            AS "VIN",
                price          AS "Price",
                condition      AS "Condition",
                features       AS "Features",
                location       AS "Location",
                photo_url      AS "Photo"
            FROM store;
            """,
            conn,
        )

    # Ensure all expected columns exist
    for col in ALL_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA

    # Type clean-up
    for col in NUM_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in TEXT_COLS:
        df[col] = df[col].astype("string").str.strip()

    return df[[c for c in ALL_COLUMNS if c in df.columns]]

def fmt_money(x):
    try:
        return f"${int(round(float(x))):,}"
    except:
        return "—"

def fmt_km(x):
    try:
        return f"{int(round(float(x))):,} km"
    except:
        return "—"

def feature_chips(features: str) -> str:
    if features is pd.NA:
        return ""
    parts = [p.strip() for p in str(features).replace("|",";").split(";") if p.strip()]
    return "".join(f'<span class="chip">{escape(p)}</span>' for p in parts[:12])

def numeric_bounds(s: pd.Series, default=(0,1)):
    s = pd.to_numeric(s, errors="coerce").dropna()
    if s.empty:
        return default
    lo, hi = int(s.min()), int(s.max())
    return (lo, hi if lo != hi else lo+1)

def text_match(row, fields, q):
    q = (q or "").lower().strip()
    if not q:
        return True
    return any(q in str(row.get(f,"")).lower() for f in fields)

def apply_multi_filter(df, col, values):
    return df[df[col].isin(values)] if values else df

# ====================== LOAD ======================
try:
    df = load_db(DB_URL)
except Exception as e:
    st.error(f"Error loading data from database: {e}")
    st.stop()

# ====================== UI ======================
st.title("🚗 Browse Inventory")

# ---- sidebar ----
with st.sidebar:
    st.header("Filters")
    q = st.text_input("Search (Make / Model / VIN / StockNo)")

    def ms(label, col):
        opts = sorted(df[col].dropna().unique()) if col in df else []
        return st.multiselect(label, opts)

    f_make = ms("Make", "Make")
    f_body = ms("BodyStyle", "BodyStyle")
    f_fuel = ms("Fuel", "Fuel")
    f_drive = ms("Drivetrain", "Drivetrain")
    f_cond = ms("Condition", "Condition")
    f_loc  = ms("Location", "Location")

    if "Price" in df:
        lo, hi = numeric_bounds(df["Price"], (0,100000))
        f_price = st.slider("Price", lo, hi, (lo, hi))
    else:
        f_price = None

    if "Mileage" in df:
        lo, hi = numeric_bounds(df["Mileage"], (0,300000))
        f_mileage = st.slider("Mileage", lo, hi, (lo, hi))
    else:
        f_mileage = None

    if "Year" in df:
        lo, hi = numeric_bounds(df["Year"], (1990,2035))
        f_year = st.slider("Year", lo, hi, (lo, hi))
    else:
        f_year = None

    sort_by = st.selectbox("Sort by", ["Price","Year","Mileage","Make","Model","StockNo"])
    sort_dir = st.radio("Order", ["Ascending","Descending"], index=1)
    per_page = st.select_slider("Cards per page", [6,9,12,15,18,24], value=12)

# ---- filtering ----
filtered = df.copy()
filtered = filtered[filtered.apply(
    lambda r: text_match(r, ["Make","Model","Trim","StockNo","VIN"], q),
    axis=1
)]

for col, val in [
    ("Make", f_make),
    ("BodyStyle", f_body),
    ("Fuel", f_fuel),
    ("Drivetrain", f_drive),
    ("Condition", f_cond),
    ("Location", f_loc),
]:
    filtered = apply_multi_filter(filtered, col, val)

if f_price:
    filtered = filtered[(filtered["Price"] >= f_price[0]) & (filtered["Price"] <= f_price[1])]
if f_mileage:
    filtered = filtered[(filtered["Mileage"] >= f_mileage[0]) & (filtered["Mileage"] <= f_mileage[1])]
if f_year:
    filtered = filtered[(filtered["Year"] >= f_year[0]) & (filtered["Year"] <= f_year[1])]

filtered = filtered.sort_values(sort_by, ascending=(sort_dir=="Ascending"))

# ---- pagination ----
total = len(filtered)
pages = max(1, math.ceil(total / per_page))
st.caption(f"{total} cars found")

if "page_no" not in st.session_state:
    st.session_state.page_no = 1
st.number_input("Page", 1, pages, key="page_no")

page_no = st.session_state.page_no
start = (page_no-1)*per_page
view = filtered.iloc[start:start+per_page].reset_index(drop=True)

# ---- style ----
st.markdown("""
<style>
.card{border:1px solid #ccc;border-radius:12px;padding:14px;margin-bottom:18px;}
.badge{padding:3px 7px;background:#eee;border-radius:999px;margin-right:4px;}
.chip{background:#edf1f5;padding:4px 8px;border-radius:999px;margin:2px 4px;display:inline-block}
</style>
""", unsafe_allow_html=True)

# ---- grid ----
cols_per_row = 3
for i in range(0, len(view), cols_per_row):
    row = view.iloc[i:i+cols_per_row]
    cols = st.columns(len(row))
    for col, (_, r) in zip(cols, row.iterrows()):
        with col:
            title = f"{r.Year or ''} {r.Make} {r.Model} {r.Trim}".strip()
            st.markdown('<div class="card">', unsafe_allow_html=True)

            if isinstance(r.Photo, str) and r.Photo.startswith(("http://","https://")):
                st.image(r.Photo)

            st.markdown(f"**{escape(title)}**")
            st.markdown(f"Price: {fmt_money(r.Price)}")
            st.markdown(f"Mileage: {fmt_km(r.Mileage)}")
            st.markdown(f"Stock#: {r.StockNo}")

            chips = feature_chips(r.Features)
            if chips:
                st.markdown(chips, unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)
