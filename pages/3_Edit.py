from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st

DB_PATH = Path("/workspaces/daner/store.db")

ALL_COLUMNS = [
    "StockNo","Make","Model","Year","Trim","BodyStyle","Transmission","Fuel","Engine","Drivetrain",
    "Mileage","ExteriorColor","InteriorColor","VIN","Price","Condition","Features","Location","Photo"
]

TEXT_COLS = [
    "StockNo","Make","Model","Trim","BodyStyle","Transmission","Fuel","Engine","Drivetrain",
    "ExteriorColor","InteriorColor","VIN","Condition","Features","Location","Photo"
]

NUM_COLS = ["Year","Mileage","Price"]

# =============== HELPERS ===============

@st.cache_data
def load_df(p: Path) -> pd.DataFrame:
    if not p.exists():
        raise FileNotFoundError(f"{p} not found")

    conn = sqlite3.connect(p)
    try:
        df = pd.read_sql(
            """
            SELECT
                StockNo,
                Make,
                Model,
                Year,
                Trim,
                BodyStyle,
                Transmission,
                Fuel,
                Engine,
                Drivetrain,
                Mileage,
                ExteriorColor,
                InteriorColor,
                VIN,
                Price,
                Condition,
                Features,
                Location,
                Photo_URL AS Photo
            FROM Store
            """,
            conn,
        )
    finally:
        conn.close()

    # Ensure all expected cols exist
    for c in ALL_COLUMNS:
        if c not in df:
            df[c] = pd.NA

    # Types
    for c in TEXT_COLS:
        df[c] = df[c].astype("string")

    for c in NUM_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    return df[ALL_COLUMNS]


def upsert_rows(p: Path, full_df: pd.DataFrame, edited_df: pd.DataFrame, q: str):
    conn = sqlite3.connect(p)
    try:
        cur = conn.cursor()

        # If not filtered (no search), we also support deletions:
        if not q:
            before = set(full_df["StockNo"].astype(str))
            after = set(edited_df["StockNo"].astype(str))
            to_delete = before - after
            if to_delete:
                cur.executemany(
                    "DELETE FROM Store WHERE StockNo = ?",
                    [(s,) for s in to_delete if s],
                )

        # For both filtered/unfiltered: UPSERT edited rows
        for _, row in edited_df.iterrows():
            stock = str(row.get("StockNo") or "").strip()
            if not stock:
                # skip rows without StockNo
                continue

            # Coerce numeric values
            def n_int(val):
                return int(val) if pd.notna(val) else None

            def n_float(val):
                return float(val) if pd.notna(val) else None

            cur.execute(
                """
                INSERT INTO Store (
                    StockNo, Make, Model, Year, Trim, BodyStyle, Transmission, Fuel,
                    Engine, Drivetrain, Mileage, ExteriorColor, InteriorColor, VIN,
                    Price, Condition, Features, Location, Photo_URL
                )
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(StockNo) DO UPDATE SET
                    Make=excluded.Make,
                    Model=excluded.Model,
                    Year=excluded.Year,
                    Trim=excluded.Trim,
                    BodyStyle=excluded.BodyStyle,
                    Transmission=excluded.Transmission,
                    Fuel=excluded.Fuel,
                    Engine=excluded.Engine,
                    Drivetrain=excluded.Drivetrain,
                    Mileage=excluded.Mileage,
                    ExteriorColor=excluded.ExteriorColor,
                    InteriorColor=excluded.InteriorColor,
                    VIN=excluded.VIN,
                    Price=excluded.Price,
                    Condition=excluded.Condition,
                    Features=excluded.Features,
                    Location=excluded.Location,
                    Photo_URL=excluded.Photo_URL
                """,
                (
                    stock,
                    row.get("Make"),
                    row.get("Model"),
                    n_int(row.get("Year")),
                    row.get("Trim"),
                    row.get("BodyStyle"),
                    row.get("Transmission"),
                    row.get("Fuel"),
                    row.get("Engine"),
                    row.get("Drivetrain"),
                    n_int(row.get("Mileage")),
                    row.get("ExteriorColor"),
                    row.get("InteriorColor"),
                    row.get("VIN"),
                    n_float(row.get("Price")),
                    row.get("Condition"),
                    row.get("Features"),
                    row.get("Location"),
                    row.get("Photo"),  # mapped to Photo_URL
                ),
            )

        conn.commit()
    finally:
        conn.close()


# =============== UI ===============

st.title("✏️ Edit Data")

if not DB_PATH.exists():
    st.error("Database not found. Make sure /workspaces/daner/store.db exists.")
    st.stop()

try:
    df = load_df(DB_PATH)
except Exception as e:
    st.error(f"Error loading data from DB: {e}")
    st.stop()

q = st.text_input("Search rows (optional)")
work = df.copy()
if q:
    work = work[work.apply(lambda r: q.lower() in str(r).lower(), axis=1)]

# Ensure types for the editor
for c in TEXT_COLS:
    work[c] = work[c].astype("string")
for c in NUM_COLS:
    work[c] = pd.to_numeric(work[c], errors="coerce")

edited = st.data_editor(
    work,
    hide_index=True,
    width='stretch',
    disabled=["StockNo"],  # keep primary key stable
)

if st.button("💾 Save Changes", type="primary"):
    try:
        upsert_rows(DB_PATH, df, edited, q)
        # Clear cache so next load sees DB updates
        load_df.clear()
        st.success("Saved changes to database.")
        st.experimental_rerun()
    except Exception as e:
        st.error(f"Error saving changes: {e}")
