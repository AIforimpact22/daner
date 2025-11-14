from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st

DB_PATH = Path("/workspaces/daner/store.db")

ALL_COLUMNS = [
    "StockNo","Make","Model","Year","Trim","BodyStyle","Transmission","Fuel","Engine","Drivetrain",
    "Mileage","ExteriorColor","InteriorColor","VIN","Price","Condition","Features","Location","Photo"
]

@st.cache_data
def load_existing_stocknos(p: Path):
    """Load existing StockNo values from the Store table."""
    if not p.exists():
        return set()
    conn = sqlite3.connect(p)
    try:
        df = pd.read_sql("SELECT StockNo FROM Store", conn)
    finally:
        conn.close()
    return set(df["StockNo"].astype(str))

def insert_car(p: Path, car: dict):
    """Insert a new car into the Store table."""
    conn = sqlite3.connect(p)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO Store (
                StockNo, Make, Model, Year, Trim, BodyStyle, Transmission, Fuel,
                Engine, Drivetrain, Mileage, ExteriorColor, InteriorColor, VIN,
                Price, Condition, Features, Location, Photo_URL
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                car["StockNo"],
                car["Make"],
                car["Model"],
                int(car["Year"]),
                car["Trim"],
                car["BodyStyle"],
                car["Transmission"],
                car["Fuel"],
                car["Engine"],
                car["Drivetrain"],
                int(car["Mileage"]),
                car["ExteriorColor"],
                car["InteriorColor"],
                car["VIN"],
                float(car["Price"]),
                car["Condition"],
                car["Features"],
                car["Location"],
                car["Photo"],       # mapped to Photo_URL in DB
            ),
        )
        conn.commit()
    finally:
        conn.close()

st.title("➕ Add Car")

if not DB_PATH.exists():
    st.error("Database not found. Make sure /workspaces/daner/store.db exists.")
    st.stop()

existing_stocknos = load_existing_stocknos(DB_PATH)

with st.form("add"):
    stock = st.text_input("StockNo *")
    make  = st.text_input("Make *")
    model = st.text_input("Model *")
    year  = st.number_input("Year *", 1900, 2100, 2020)
    price = st.number_input("Price *", 1, 2_000_000, 1000)
    trim = st.text_input("Trim")
    body = st.text_input("BodyStyle")
    trans = st.text_input("Transmission")
    fuel = st.text_input("Fuel")
    eng  = st.text_input("Engine")
    drive = st.text_input("Drivetrain")
    mileage = st.number_input("Mileage", 0, 2_000_000, 0)
    ext = st.text_input("ExteriorColor")
    inc = st.text_input("InteriorColor")
    vin = st.text_input("VIN (17 chars)")
    cond = st.text_input("Condition")
    feats = st.text_input("Features (semicolon separated)")
    loc = st.text_input("Location")
    photo = st.text_input("Photo (URL)")

    sub = st.form_submit_button("Save")

if sub:
    errs = []
    if not stock:
        errs.append("StockNo required.")
    if not make:
        errs.append("Make required.")
    if not model:
        errs.append("Model required.")
    if vin and len(vin) != 17:
        errs.append("VIN must be 17 chars.")

    if stock and stock in existing_stocknos:
        errs.append(f"StockNo `{stock}` already exists.")

    if errs:
        for e in errs:
            st.error(e)
    else:
        new = {
            "StockNo": stock,
            "Make": make,
            "Model": model,
            "Year": year,
            "Trim": trim,
            "BodyStyle": body,
            "Transmission": trans,
            "Fuel": fuel,
            "Engine": eng,
            "Drivetrain": drive,
            "Mileage": mileage,
            "ExteriorColor": ext,
            "InteriorColor": inc,
            "VIN": vin,
            "Price": price,
            "Condition": cond,
            "Features": feats,
            "Location": loc,
            "Photo": photo,   # will be saved as Photo_URL in DB
        }

        try:
            insert_car(DB_PATH, new)
            # clear cache so next add sees the new StockNo
            load_existing_stocknos.clear()
            st.success(f"Saved `{stock}`")
        except Exception as e:
            st.error(f"Error saving car: {e}")
