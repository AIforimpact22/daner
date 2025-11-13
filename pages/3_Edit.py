from pathlib import Path
import pandas as pd
import streamlit as st

DATA_PATH = Path("/workspaces/daner/data.csv")

ALL_COLUMNS = [
    "StockNo","Make","Model","Year","Trim","BodyStyle","Transmission","Fuel","Engine","Drivetrain",
    "Mileage","ExteriorColor","InteriorColor","VIN","Price","Condition","Features","Location","Photo"
]

TEXT_COLS = [
    "StockNo","Make","Model","Trim","BodyStyle","Transmission","Fuel","Engine","Drivetrain",
    "ExteriorColor","InteriorColor","VIN","Condition","Features","Location","Photo"
]

NUM_COLS = ["Year","Mileage","Price"]

@st.cache_data
def load_csv(p: Path):
    df = pd.read_csv(p)
    for c in ALL_COLUMNS:
        if c not in df: df[c] = pd.NA
    return df[ALL_COLUMNS]

def save_csv(df,p):
    df.to_csv(p, index=False)

st.title("✏️ Edit Data")

if not DATA_PATH.exists():
    st.error("CSV not found. Upload it first.")
    st.stop()

df = load_csv(DATA_PATH)

q = st.text_input("Search rows (optional)")
work = df.copy()
if q:
    work = work[work.apply(lambda r:
        q.lower() in str(r).lower(), axis=1)]

for c in TEXT_COLS:
    work[c] = work[c].astype("string")
for c in NUM_COLS:
    work[c] = pd.to_numeric(work[c], errors="coerce")

edited = st.data_editor(work, hide_index=True, width='stretch')

if st.button("💾 Save Changes", type="primary"):
    if q:
        df.loc[edited.index, :] = edited
    else:
        df = edited

    save_csv(df, DATA_PATH)
    st.success("Saved CSV.")
    st.experimental_rerun()
