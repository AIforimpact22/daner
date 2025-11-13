from pathlib import Path
import pandas as pd
import streamlit as st

DATA_PATH = Path("/workspaces/daner/data.csv")

ALL_COLUMNS = [
    "StockNo","Make","Model","Year","Trim","BodyStyle","Transmission","Fuel","Engine","Drivetrain",
    "Mileage","ExteriorColor","InteriorColor","VIN","Price","Condition","Features","Location","Photo"
]

@st.cache_data
def load_csv(p: Path):
    df = pd.read_csv(p)
    for c in ALL_COLUMNS:
        if c not in df: df[c] = pd.NA
    return df[ALL_COLUMNS]

def save_csv(df, p): df.to_csv(p, index=False)

st.title("➕ Add Car")

if DATA_PATH.exists():
    df = load_csv(DATA_PATH)
else:
    st.error("CSV not found. Please go to Browse page and upload one.")
    st.stop()

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
    if not stock: errs.append("StockNo required.")
    if not make: errs.append("Make required.")
    if not model: errs.append("Model required.")
    if vin and len(vin) != 17: errs.append("VIN must be 17 chars.")

    if stock in df.StockNo.astype(str).values:
        errs.append(f"StockNo `{stock}` already exists.")

    if errs:
        for e in errs: st.error(e)
    else:
        new = {
            "StockNo":stock, "Make":make, "Model":model, "Year":year, "Trim":trim,
            "BodyStyle":body, "Transmission":trans, "Fuel":fuel, "Engine":eng,
            "Drivetrain":drive, "Mileage":mileage, "ExteriorColor":ext,
            "InteriorColor":inc, "VIN":vin, "Price":price, "Condition":cond,
            "Features":feats, "Location":loc, "Photo":photo
        }
        df2 = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
        save_csv(df2, DATA_PATH)
        st.success(f"Saved `{stock}`")
