# app.py
from __future__ import annotations
import math
from pathlib import Path
from html import escape

import pandas as pd
import streamlit as st

# ====================== CONFIG ======================
st.set_page_config(page_title="Car Inventory", page_icon="🚗", layout="wide")
DATA_PATH = Path("/workspaces/daner/data.csv")

# Canonical columns (Photo is optional but supported)
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
def load_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    # ensure all expected columns exist
    for col in ALL_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA
    # coerce dtypes
    for col in NUM_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in TEXT_COLS:
        if col in df.columns:
            df[col] = df[col].astype("string")
    # strip spaces in text
    for col in TEXT_COLS:
        if col in df.columns:
            df[col] = df[col].astype("string").str.strip()
    # reorder
    return df[[c for c in ALL_COLUMNS if c in df.columns]]

def save_csv(df: pd.DataFrame, path: Path) -> None:
    # normalize before save
    out = df.copy()
    for col in ALL_COLUMNS:
        if col not in out.columns:
            out[col] = pd.NA
    for col in NUM_COLS:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    for col in TEXT_COLS:
        if col in out.columns:
            out[col] = out[col].astype("string")
    out = out[ALL_COLUMNS]
    out.to_csv(path, index=False)

def fmt_money(x) -> str:
    try:
        return f"${int(round(float(x))):,}"
    except Exception:
        return "—"

def fmt_km(x) -> str:
    try:
        return f"{int(round(float(x))):,} km"
    except Exception:
        return "—"

def feature_chips(features: str) -> str:
    if features is pd.NA or features is None:
        return ""
    s = str(features) if not pd.isna(features) else ""
    parts = [p.strip() for p in s.replace("|",";").split(";") if p.strip()]
    return "".join(f'<span class="chip">{escape(p)}</span>' for p in parts[:12])

def numeric_bounds(s: pd.Series, default=(0,1)):
    s = pd.to_numeric(s, errors="coerce").dropna()
    if s.empty:
        return default
    lo, hi = int(s.min()), int(s.max())
    if lo == hi:
        hi = lo + 1
    return lo, hi

def text_match(row: pd.Series, fields: list[str], q: str) -> bool:
    q = (q or "").lower().strip()
    if not q:
        return True
    for f in fields:
        if q in str(row.get(f,"")).lower():
            return True
    return False

def apply_multi_filter(data: pd.DataFrame, col: str, values: list) -> pd.DataFrame:
    if values and col in data.columns:
        return data[data[col].isin(values)]
    return data

def coerce_for_save(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    # strings
    for col in TEXT_COLS:
        if col in out.columns:
            out[col] = out[col].astype("string").str.strip()
            out[col] = out[col].replace({"": pd.NA})
    # numerics
    for col in NUM_COLS:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out

def validate_rows(df: pd.DataFrame) -> list[str]:
    errors = []
    if "StockNo" not in df.columns:
        errors.append("Missing required column: StockNo")
        return errors
    for idx, row in df.iterrows():
        row_id = f"row {idx+1}"
        if not str(row.get("StockNo", "")).strip():
            errors.append(f"{row_id}: StockNo is required.")
        if not str(row.get("Make", "")).strip():
            errors.append(f"{row_id}: Make is required.")
        if not str(row.get("Model", "")).strip():
            errors.append(f"{row_id}: Model is required.")
        y = row.get("Year", pd.NA)
        if pd.isna(y):
            errors.append(f"{row_id}: Year is required.")
        else:
            try:
                yi = int(y)
                if yi < 1900 or yi > 2100:
                    errors.append(f"{row_id}: Year must be between 1900 and 2100.")
            except Exception:
                errors.append(f"{row_id}: Year must be a number.")
        p = row.get("Price", pd.NA)
        if pd.isna(p):
            errors.append(f"{row_id}: Price is required.")
        else:
            try:
                if float(p) <= 0:
                    errors.append(f"{row_id}: Price must be > 0.")
            except Exception:
                errors.append(f"{row_id}: Price must be numeric.")
        vin = str(row.get("VIN", "")).strip()
        if vin and len(vin) != 17:
            errors.append(f"{row_id}: VIN should be 17 characters (optional but if set, must be 17).")
    # Unique StockNo
    if df["StockNo"].astype(str).duplicated().any():
        dups = df["StockNo"].astype(str)[df["StockNo"].astype(str).duplicated(keep=False)].tolist()
        errors.append(f"Duplicate StockNo values found: {sorted(set(dups))}")
    return errors

# ====================== LOAD DATA ======================
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Browse", "Add New", "Edit Data"])

if DATA_PATH.exists():
    df = load_csv(DATA_PATH)
else:
    st.warning(f"Could not find `{DATA_PATH}`. Upload your CSV to continue.")
    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    if not uploaded:
        st.stop()
    df = pd.read_csv(uploaded)
    # normalize like load_csv
    for col in ALL_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA
    for col in NUM_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in TEXT_COLS:
        if col in df.columns:
            df[col] = df[col].astype("string").str.strip()
    df = df[[c for c in ALL_COLUMNS if c in df.columns]]

# ====================== BROWSE PAGE ======================
if page == "Browse":
    st.title("🚗 Car Inventory — Browse")

    # ---- Sidebar filters ----
    with st.sidebar:
        st.header("Filters")
        q = st.text_input("Search", placeholder="Make / Model / Trim / StockNo / VIN")

        def ms(label, col):
            if col in df.columns:
                opts = sorted(x for x in df[col].dropna().unique())
                return st.multiselect(label, opts, key=f"ms_{col}")
            return []

        f_make      = ms("Make", "Make")
        f_body      = ms("Body Style", "BodyStyle")
        f_fuel      = ms("Fuel", "Fuel")
        f_drive     = ms("Drivetrain", "Drivetrain")
        f_condition = ms("Condition", "Condition")
        f_location  = ms("Location", "Location")

        f_price = None
        if "Price" in df.columns:
            pmin, pmax = numeric_bounds(df["Price"], (0, 100000))
            f_price = st.slider("Price", pmin, pmax, (pmin, pmax), step=500, key="sl_price")

        f_mileage = None
        if "Mileage" in df.columns:
            mmin, mmax = numeric_bounds(df["Mileage"], (0, 300000))
            f_mileage = st.slider("Mileage", mmin, mmax, (mmin, mmax), step=1000, key="sl_mileage")

        f_year = None
        if "Year" in df.columns:
            ymin, ymax = numeric_bounds(df["Year"], (1990, 2035))
            f_year = st.slider("Year", ymin, ymax, (ymin, ymax), step=1, key="sl_year")

        st.header("View")
        sort_options = [c for c in ["Price","Year","Mileage","Make","Model","StockNo"] if c in df.columns]
        sort_by = st.selectbox("Sort by", sort_options, index=0 if sort_options else 0, key="sort_by")
        sort_dir = st.radio("Order", ["Ascending","Descending"], horizontal=True, index=1, key="sort_dir")
        per_page = st.select_slider("Cards per page", [6,9,12,15,18,24], value=12, key="per_page")

    # ---- Apply filters ----
    filtered = df.copy()
    filtered = filtered[filtered.apply(lambda row: text_match(row,
                                                             ["Make","Model","Trim","StockNo","VIN"],
                                                             q), axis=1)]
    filtered = apply_multi_filter(filtered, "Make", f_make)
    filtered = apply_multi_filter(filtered, "BodyStyle", f_body)
    filtered = apply_multi_filter(filtered, "Fuel", f_fuel)
    filtered = apply_multi_filter(filtered, "Drivetrain", f_drive)
    filtered = apply_multi_filter(filtered, "Condition", f_condition)
    filtered = apply_multi_filter(filtered, "Location", f_location)

    if f_price and "Price" in filtered.columns:
        filtered = filtered[(filtered["Price"] >= f_price[0]) & (filtered["Price"] <= f_price[1])]
    if f_mileage and "Mileage" in filtered.columns:
        filtered = filtered[(filtered["Mileage"] >= f_mileage[0]) & (filtered["Mileage"] <= f_mileage[1])]
    if f_year and "Year" in filtered.columns:
        filtered = filtered[(filtered["Year"] >= f_year[0]) & (filtered["Year"] <= f_year[1])]

    if sort_options:
        filtered = filtered.sort_values(by=sort_by, ascending=(sort_dir=="Ascending"), kind="mergesort")

    # ---- Pagination ----
    total = len(filtered)
    pages = max(1, math.ceil(total / per_page))
    if "page_no" not in st.session_state:
        st.session_state.page_no = 1
    st.caption(f"{total} result{'s' if total != 1 else ''}", help="Number of cars after filters")
    st.number_input("Page", min_value=1, max_value=pages, step=1, key="page_no")
    page_no = st.session_state.page_no
    start, end = (page_no-1)*per_page, (page_no-1)*per_page + per_page
    view = filtered.iloc[start:end].reset_index(drop=True)
    st.caption(f"Showing {start+1}–{min(end, total)} of {total}")

    # ---- Styles ----
    st.markdown("""
    <style>
    .card { border: 1px solid rgba(0,0,0,0.08); border-radius: 12px; padding: 16px;
            margin-bottom: 18px; background: var(--background, #fff);
            box-shadow: 0 1px 2px rgba(0,0,0,0.04); }
    .card:hover { box-shadow: 0 4px 14px rgba(0,0,0,0.1); }
    .title { font-size: 1.05rem; font-weight: 700; margin-bottom: 2px; }
    .subtitle { color: rgba(0,0,0,0.6); font-size: 0.9rem; margin-bottom: 10px; }
    .price { font-weight: 800; font-size: 1.1rem; margin-bottom: 8px; }
    .badge { display: inline-block; padding: 2px 8px; margin-right: 6px; border-radius: 999px;
             font-size: 0.75rem; background: rgba(0,0,0,0.06); }
    .chip { display: inline-block; background: rgba(0,0,0,0.06);
            padding: 4px 8px; border-radius: 999px; margin: 2px 6px 2px 0; font-size: 0.75rem; }
    .kv { font-size: 0.85rem; margin-top: 6px; }
    .kv b { color: rgba(0,0,0,0.75); }
    .loc { color: rgba(0,0,0,0.7); font-size: 0.85rem; }
    </style>
    """, unsafe_allow_html=True)

    # ---- Metrics ----
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Total Cars", total)
    with c2:
        if "Price" in filtered.columns and not filtered["Price"].dropna().empty:
            st.metric("Median Price", fmt_money(filtered["Price"].median()))
    with c3:
        if "Mileage" in filtered.columns and not filtered["Mileage"].dropna().empty:
            st.metric("Median Mileage", fmt_km(filtered["Mileage"].median()))

    # ---- Cards Grid ----
    cols_per_row = 3
    for i in range(0, len(view), cols_per_row):
        chunk = view.iloc[i:i+cols_per_row]
        cols = st.columns(len(chunk))
        for col, (_, r) in zip(cols, chunk.iterrows()):
            with col:
                year  = r.get("Year", "")
                make  = r.get("Make", "")
                model = r.get("Model", "")
                trim  = r.get("Trim", "")
                body  = r.get("BodyStyle", "")
                drive = r.get("Drivetrain", "")
                trans = r.get("Transmission", "")
                price = r.get("Price", "")
                cond  = r.get("Condition", "")
                fuel  = r.get("Fuel", "")
                mil   = r.get("Mileage", "")
                eng   = r.get("Engine", "")
                extc  = r.get("ExteriorColor", "")
                intc  = r.get("InteriorColor", "")
                stock = r.get("StockNo", "")
                vin   = r.get("VIN", "")
                loc   = r.get("Location", "")
                feats = r.get("Features", "")
                photo = r.get("Photo", "")

                title = f"{int(year) if pd.notna(year) else ''} {make} {model} {trim}".strip()
                subtitle = " • ".join([x for x in [str(body or "").strip(),
                                                    str(drive or "").strip(),
                                                    str(trans or "").strip()] if x])

                st.markdown('<div class="card">', unsafe_allow_html=True)
                # (No deprecated param; Streamlit's deprecation warning was for use_container_width.)
                if isinstance(photo, str) and photo.lower().startswith(("http://","https://")):
                    st.image(photo)

                st.markdown(f'<div class="title">{escape(title)}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="subtitle">{escape(subtitle)}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="price">{fmt_money(price)}</div>', unsafe_allow_html=True)

                badges = []
                if cond: badges.append(str(cond))
                if fuel: badges.append(str(fuel))
                if mil and not pd.isna(mil): badges.append(fmt_km(mil))
                if badges:
                    st.markdown(" ".join(f'<span class="badge">{escape(b)}</span>' for b in badges),
                                unsafe_allow_html=True)

                st.markdown(
                    f'<div class="kv"><b>Engine:</b> {escape(str(eng or "—"))} &nbsp; '
                    f'<b>Ext:</b> {escape(str(extc or "—"))} &nbsp; '
                    f'<b>Int:</b> {escape(str(intc or "—"))}</div>',
                    unsafe_allow_html=True
                )

                chips = feature_chips(feats)
                if chips:
                    st.markdown(chips, unsafe_allow_html=True)

                st.markdown(
                    f'<div class="kv"><b>Stock#</b> {escape(str(stock or "—"))} &nbsp; '
                    f'<b>VIN</b> {escape(str(vin or "—"))}</div>',
                    unsafe_allow_html=True
                )
                if loc:
                    st.markdown(f'<div class="loc">📍 {escape(str(loc))}</div>', unsafe_allow_html=True)

                with st.expander("Details"):
                    st.json({k: (None if pd.isna(v) else v) for k, v in r.items()})

                st.markdown('</div>', unsafe_allow_html=True)

    st.caption("Tip: Add a 'Photo' column with an image URL to show pictures in each card.")

# ====================== ADD NEW PAGE ======================
if page == "Add New":
    st.title("➕ Add a New Car")
    st.info("Fields marked with * are required. Separate Features with semicolons (e.g., `Bluetooth;Backup Camera`).")

    get_opts = lambda col: (sorted([x for x in df[col].dropna().unique()]) if col in df.columns else [])
    existing_makes = get_opts("Make")
    existing_bodies = get_opts("BodyStyle")
    existing_trans  = get_opts("Transmission")
    existing_fuels  = get_opts("Fuel")
    existing_drive  = get_opts("Drivetrain")
    existing_cond   = get_opts("Condition")
    existing_loc    = get_opts("Location")

    with st.form("new_car_form", clear_on_submit=False):
        c1, c2, c3 = st.columns(3)

        with c1:
            stockno = st.text_input("StockNo *", placeholder="e.g., A031").strip()
            make = st.selectbox("Make *", [""] + existing_makes, index=0)
            model = st.text_input("Model *", placeholder="e.g., Corolla").strip()
            year = st.number_input("Year *", min_value=1900, max_value=2100, value=2021, step=1)
            trim = st.text_input("Trim", placeholder="e.g., LE").strip()
            price = st.number_input("Price *", min_value=1, max_value=2_000_000, value=1000, step=100)

        with c2:
            bodystyle = st.selectbox("BodyStyle", [""] + existing_bodies, index=0)
            transmission = st.selectbox("Transmission", ["", "Automatic", "Manual", "CVT"] +
                                        [x for x in existing_trans if x not in ["Automatic","Manual","CVT"]], index=0)
            fuel = st.selectbox("Fuel", ["", "Petrol", "Diesel", "Hybrid", "Electric"] +
                                [x for x in existing_fuels if x not in ["Petrol","Diesel","Hybrid","Electric"]], index=0)
            engine = st.text_input("Engine", placeholder="e.g., 1.8L I4").strip()
            drivetrain = st.selectbox("Drivetrain", ["", "FWD", "RWD", "AWD", "4x4"] +
                                      [x for x in existing_drive if x not in ["FWD","RWD","AWD","4x4"]], index=0)
            mileage = st.number_input("Mileage", min_value=0, max_value=2_000_000, value=0, step=500)

        with c3:
            exterior = st.text_input("ExteriorColor", placeholder="e.g., Silver").strip()
            interior = st.text_input("InteriorColor", placeholder="e.g., Black").strip()
            vin = st.text_input("VIN", placeholder="17 characters").strip()
            condition = st.selectbox("Condition", ["", "Used", "New", "CPO"] +
                                     [x for x in existing_cond if x not in ["Used","New","CPO"]], index=1 if "Used" in existing_cond else 0)
            features = st.text_input("Features", placeholder="e.g., Bluetooth;Backup Camera;Apple CarPlay").strip()
            location = st.selectbox("Location", [""] + (existing_loc or ["Budapest, HU"]), index=1 if existing_loc else 0)

        photo = st.text_input("Photo (URL)", placeholder="https://... (optional)").strip()

        submitted = st.form_submit_button("Save Car", width='stretch')

    if submitted:
        errors = []
        if not stockno: errors.append("StockNo is required.")
        if not make: errors.append("Make is required.")
        if not model: errors.append("Model is required.")
        if not year: errors.append("Year is required.")
        if price is None or price <= 0: errors.append("Price must be greater than 0.")
        if stockno and "StockNo" in df.columns and stockno in set(df["StockNo"].astype(str)):
            errors.append(f"StockNo `{stockno}` already exists.")
        if vin and len(vin) != 17:
            errors.append("VIN should be exactly 17 characters.")

        if errors:
            for e in errors: st.error(e)
        else:
            new_row = {
                "StockNo": stockno,
                "Make": make,
                "Model": model,
                "Year": int(year) if year else pd.NA,
                "Trim": trim or pd.NA,
                "BodyStyle": bodystyle or pd.NA,
                "Transmission": transmission or pd.NA,
                "Fuel": fuel or pd.NA,
                "Engine": engine or pd.NA,
                "Drivetrain": drivetrain or pd.NA,
                "Mileage": int(mileage) if mileage else pd.NA,
                "ExteriorColor": exterior or pd.NA,
                "InteriorColor": interior or pd.NA,
                "VIN": vin or pd.NA,
                "Price": float(price) if price is not None else pd.NA,
                "Condition": condition or pd.NA,
                "Features": features or pd.NA,
                "Location": location or pd.NA,
                "Photo": photo or pd.NA,
            }

            try:
                st.cache_data.clear()
                if DATA_PATH.exists():
                    cur = load_csv(DATA_PATH)
                    cur = pd.concat([cur, pd.DataFrame([new_row])], ignore_index=True)
                    save_csv(cur, DATA_PATH)
                else:
                    save_csv(pd.DataFrame([new_row], columns=ALL_COLUMNS), DATA_PATH)

                st.success(f"Saved car `{stockno}` ✅")
                st.json(new_row)
                if st.button("Go to Browse", type="primary", width='stretch'):
                    st.session_state.page_no = 1
                    st.experimental_rerun()

            except Exception as ex:
                st.error(f"Failed to save: {ex}")

# ====================== EDIT DATA PAGE ======================
if page == "Edit Data":
    st.title("✏️ Edit Data")
    st.caption("Edit values in the table below, then click **Save Changes**. "
               "Validation checks will run before saving to the CSV.")

    q = st.text_input("Filter rows (optional)", placeholder="Search Make / Model / StockNo / VIN")
    working = df.copy()
    if q:
        working = working[working.apply(lambda row: text_match(row, ["Make","Model","Trim","StockNo","VIN"], q), axis=1)]

    # Ensure editor-friendly dtypes (this fixes the Photo=text vs float issue)
    for col in TEXT_COLS:
        if col in working.columns:
            working[col] = working[col].astype("string")
    for col in NUM_COLS:
        if col in working.columns:
            working[col] = pd.to_numeric(working[col], errors="coerce")

    # Column configs
    col_cfg = {
        "Year": st.column_config.NumberColumn("Year", min_value=1900, max_value=2100, step=1),
        "Mileage": st.column_config.NumberColumn("Mileage", min_value=0, max_value=2_000_000, step=100),
        "Price": st.column_config.NumberColumn("Price ($)", min_value=1, max_value=2_000_000, step=100),
        "Features": st.column_config.TextColumn("Features (semicolon-separated)"),
        "Photo": st.column_config.TextColumn("Photo URL (optional)"),
        "VIN": st.column_config.TextColumn("VIN (17 chars, optional)"),
    }

    edited = st.data_editor(
        working,
        width='stretch',
        num_rows="fixed",          # keep row count steady here; use Add New page for inserts
        column_config=col_cfg,
        hide_index=True,
        key="editor_table",
    )

    # Map edited subset back to full df
    if q:
        updated_df = df.copy()
        updated_df.loc[edited.index, :] = edited
    else:
        updated_df = edited

    c1, c2 = st.columns([1,1])
    with c1:
        save_btn = st.button("💾 Save Changes", type="primary", width='stretch')
    with c2:
        reset_btn = st.button("↩️ Reset (discard unsaved)", width='stretch')

    if reset_btn:
        st.cache_data.clear()
        st.experimental_rerun()

    if save_btn:
        try:
            clean = coerce_for_save(updated_df)
            errs = validate_rows(clean)
            if errs:
                for e in errs:
                    st.error(e)
            else:
                st.cache_data.clear()
                save_csv(clean, DATA_PATH)
                st.success("Changes saved to CSV ✅")
                st.caption(str(DATA_PATH))
                st.experimental_rerun()
        except Exception as ex:
            st.error(f"Failed to save: {ex}")
