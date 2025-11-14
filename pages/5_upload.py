from __future__ import annotations
from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st

# ====================== CONFIG ======================
DB_PATH = Path("/workspaces/daner/store.db")

# Columns expected from CSV (your example)
CSV_COLUMNS = [
    "StockNo","Make","Model","Year","Trim","BodyStyle","Transmission","Fuel","Engine","Drivetrain",
    "Mileage","ExteriorColor","InteriorColor","VIN","Price","Condition","Features","Location","Photo"
]

# Columns actually in the Store table in SQLite
STORE_COLUMNS_DB = [
    "StockNo","Make","Model","Year","Trim","BodyStyle","Transmission","Fuel","Engine","Drivetrain",
    "Mileage","ExteriorColor","InteriorColor","VIN","Price","Condition","Features","Location","Photo_URL"
]

REQUIRED_COLUMNS = [
    "StockNo","Make","Model","Year","BodyStyle","Transmission","Fuel","Engine","Drivetrain",
    "Mileage","ExteriorColor","InteriorColor","VIN","Price","Condition","Location"
]

NUM_COLS = ["Year","Mileage","Price"]


# ====================== DB HELPERS ======================
def ensure_store_table(conn: sqlite3.Connection):
    """Create Store table if it does not exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS Store (
            StockNo TEXT PRIMARY KEY,
            Make TEXT,
            Model TEXT,
            Year INTEGER,
            Trim TEXT,
            BodyStyle TEXT,
            Transmission TEXT,
            Fuel TEXT,
            Engine TEXT,
            Drivetrain TEXT,
            Mileage INTEGER,
            ExteriorColor TEXT,
            InteriorColor TEXT,
            VIN TEXT,
            Price REAL,
            Condition TEXT,
            Features TEXT,
            Location TEXT,
            Photo_URL TEXT
        );
    """)


def import_csv_to_db(df: pd.DataFrame, db_path: Path) -> int:
    """
    Import dataframe into Store table, upserting by StockNo.
    Returns number of rows imported/updated.
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    ensure_store_table(conn)

    # Ensure all expected CSV columns exist in df
    for col in CSV_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA

    # Type cleaning for numeric columns
    for col in NUM_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Build rows list in the exact order of STORE_COLUMNS_DB
    rows = []
    for _, r in df.iterrows():
        rows.append((
            r.get("StockNo"),
            r.get("Make"),
            r.get("Model"),
            r.get("Year"),
            r.get("Trim"),
            r.get("BodyStyle"),
            r.get("Transmission"),
            r.get("Fuel"),
            r.get("Engine"),
            r.get("Drivetrain"),
            r.get("Mileage"),
            r.get("ExteriorColor"),
            r.get("InteriorColor"),
            r.get("VIN"),
            r.get("Price"),
            r.get("Condition"),
            r.get("Features"),
            r.get("Location"),
            r.get("Photo"),      # <-- maps CSV Photo -> DB Photo_URL
        ))

    # Replace NaNs with None so sqlite stores NULL
    rows = [
        tuple(None if (isinstance(v, float) and pd.isna(v)) or v is pd.NA else v for v in row)
        for row in rows
    ]

    # 19 columns → 19 placeholders (THIS WAS THE BUG BEFORE)
    conn.executemany(
        """
        INSERT OR REPLACE INTO Store (
            StockNo, Make, Model, Year, Trim, BodyStyle, Transmission, Fuel,
            Engine, Drivetrain, Mileage, ExteriorColor, InteriorColor, VIN,
            Price, Condition, Features, Location, Photo_URL
        )
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        rows,
    )

    conn.commit()
    conn.close()
    return len(rows)


# ====================== STREAMLIT UI ======================
st.set_page_config(page_title="Upload Inventory CSV", page_icon="📤", layout="wide")
st.title("📤 Upload Inventory to Store Table")

st.write(f"Database path: `{DB_PATH}`")

if not DB_PATH.exists():
    st.error(f"Database file not found at `{DB_PATH}`. Create it first with your DB script.")
    st.stop()

uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Error reading CSV: {e}")
        st.stop()

    # Validate required columns
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        st.error(f"CSV is missing required columns: {', '.join(missing)}")
        st.stop()

    st.subheader("Preview")
    st.dataframe(df.head())

    st.info(
        "When you click **Import to database**, rows will be "
        "inserted or updated by `StockNo` in the `Store` table."
    )

    if st.button("Import to database"):
        try:
            count = import_csv_to_db(df, DB_PATH)
            st.success(f"Imported / updated {count} rows into `Store` table.")
        except Exception as e:
            st.error(f"Error importing into database: {e}")
else:
    st.caption("Upload a CSV file with columns like: "
               "StockNo, Make, Model, Year, Trim, BodyStyle, Transmission, Fuel, Engine, "
               "Drivetrain, Mileage, ExteriorColor, InteriorColor, VIN, Price, Condition, "
               "Features, Location, Photo")
