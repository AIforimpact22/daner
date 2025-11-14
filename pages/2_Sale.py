from __future__ import annotations
from datetime import date

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

# ====================== CONFIG ======================
st.set_page_config(page_title="Record Sale", page_icon="💸", layout="centered")

# Get DB URL from Streamlit secrets (set DB_URL in .streamlit/secrets.toml)
DB_URL = st.secrets.get("DB_URL")

if not DB_URL:
    st.error("Database URL not found. Please set DB_URL in Streamlit secrets.")
    st.stop()

# ====================== DB HELPERS ======================
def get_engine():
    return create_engine(DB_URL)


@st.cache_data
def load_unsold_cars(db_url: str) -> pd.DataFrame:
    """
    Load cars from store that do not have a corresponding record in sale.
    If the sale table does not exist yet, return all cars.
    """
    engine = create_engine(db_url)
    with engine.connect() as conn:
        # Check if "sale" table exists
        has_sale = conn.execute(
            text("SELECT to_regclass('public.sale');")
        ).scalar() is not None

        if has_sale:
            query = """
                SELECT
                    s.stockno      AS "StockNo",
                    s.make         AS "Make",
                    s.model        AS "Model",
                    s.year         AS "Year",
                    s.trim         AS "Trim",
                    s.price        AS "Price",
                    s.mileage      AS "Mileage",
                    s.location     AS "Location"
                FROM store s
                WHERE NOT EXISTS (
                    SELECT 1 FROM sale sa
                    WHERE sa.stockno = s.stockno
                )
                ORDER BY s.year DESC, s.make, s.model;
            """
        else:
            query = """
                SELECT
                    s.stockno      AS "StockNo",
                    s.make         AS "Make",
                    s.model        AS "Model",
                    s.year         AS "Year",
                    s.trim         AS "Trim",
                    s.price        AS "Price",
                    s.mileage      AS "Mileage",
                    s.location     AS "Location"
                FROM store s
                ORDER BY s.year DESC, s.make, s.model;
            """

        df = pd.read_sql(text(query), conn)

    return df


def record_sale(
    stock_no: str,
    sale_date: date,
    sale_price: float,
    buyer_name: str | None,
    notes: str | None,
    salesperson_id: int | None,
):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO sale (stockno, saledate, saleprice, buyername, notes, salespersonid)
                VALUES (:stockno, :saledate, :saleprice, :buyername, :notes, :salespersonid);
                """
            ),
            {
                "stockno": stock_no,
                "saledate": sale_date,  # driver will handle date object
                "saleprice": float(sale_price),
                "buyername": buyer_name or None,
                "notes": notes or None,
                "salespersonid": salesperson_id,
            },
        )


# ====================== UI ======================
st.title("💸 Record a Car Sale")

# Load unsold cars
try:
    inventory = load_unsold_cars(DB_URL)
except Exception as e:
    st.error(f"Error loading inventory from database: {e}")
    st.stop()

if inventory.empty:
    st.info("No available cars to sell (all are sold or inventory is empty).")
    st.stop()

st.subheader("Select Vehicle")

# Build nice labels for the selectbox
def car_label(row):
    year = int(row["Year"]) if pd.notna(row["Year"]) else ""
    make = row["Make"] or ""
    model = row["Model"] or ""
    trim = row["Trim"] or ""
    price = row["Price"]
    price_txt = f"${int(price):,}" if pd.notna(price) else "N/A"
    return f"{row['StockNo']} — {year} {make} {model} {trim} ({price_txt})"

options = {
    car_label(r): r["StockNo"]
    for _, r in inventory.iterrows()
}

choice_label = st.selectbox(
    "Choose a car to sell",
    list(options.keys())
)
selected_stock_no = options[choice_label]
selected_row = inventory[inventory["StockNo"] == selected_stock_no].iloc[0]

with st.expander("Selected car details"):
    st.write(
        f"**StockNo:** {selected_row['StockNo']}\n\n"
        f"**Year:** {selected_row['Year']}\n\n"
        f"**Make / Model / Trim:** {selected_row['Make']} {selected_row['Model']} {selected_row['Trim']}\n\n"
        f"**Location:** {selected_row['Location']}\n\n"
        f"**List Price:** {selected_row['Price']}"
    )

st.subheader("Sale Details")

with st.form("sale_form"):
    sale_date = st.date_input("Sale date", value=date.today())
    default_price = float(selected_row["Price"]) if pd.notna(selected_row["Price"]) else 0.0
    sale_price = st.number_input("Sale price", min_value=0.0, value=default_price, step=500.0)

    buyer_name = st.text_input("Buyer name")
    notes = st.text_area("Notes (optional)")

    salesperson_col1, salesperson_col2 = st.columns(2)
    with salesperson_col1:
        salesperson_id_raw = st.number_input(
            "Salesperson ID (optional, from User table)",
            min_value=0,
            step=1,
            value=0,
        )
    with salesperson_col2:
        st.caption("Leave as 0 if you don't want to link to a User yet.")

    submitted = st.form_submit_button("Save Sale")

    if submitted:
        if sale_price <= 0:
            st.error("Sale price must be greater than 0.")
        else:
            salesperson_id = int(salesperson_id_raw) if salesperson_id_raw > 0 else None
            try:
                record_sale(
                    stock_no=selected_stock_no,
                    sale_date=sale_date,
                    sale_price=sale_price,
                    buyer_name=buyer_name.strip() or None,
                    notes=notes.strip() or None,
                    salesperson_id=salesperson_id,
                )
                st.success(f"Sale recorded for StockNo {selected_stock_no}.")
                st.experimental_rerun()
            except IntegrityError as e:
                st.error(f"Database integrity error: {e}")
            except Exception as e:
                st.error(f"Error recording sale: {e}")
