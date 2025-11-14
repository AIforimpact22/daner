from pathlib import Path
import sqlite3
from io import BytesIO

import pandas as pd
import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

# ======================================================
# CONFIG
# ======================================================
DB_PATH = Path("/workspaces/daner/store.db")
st.set_page_config(page_title="Compare Models", page_icon="⚖️", layout="wide")

st.title("⚖️ Compare Car Models")
st.caption("Compare two car models and instantly export a PDF report.")


# ======================================================
# HELPERS
# ======================================================
@st.cache_data
def load_df(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"{path} not found")

    conn = sqlite3.connect(path)
    try:
        df = pd.read_sql(
            """
            SELECT
                Make,
                Model,
                Trim,
                Year,
                Mileage,
                Price,
                Condition,
                Fuel,
                Engine,
                Drivetrain,
                Transmission,
                BodyStyle,
                Location,
                Photo_URL AS Photo
            FROM Store
            """,
            conn,
        )
    finally:
        conn.close()

    required = [
        "Make","Model","Trim","Year","Mileage","Price","Condition","Fuel",
        "Engine","Drivetrain","Transmission","BodyStyle","Location","Photo"
    ]
    for c in required:
        if c not in df:
            df[c] = pd.NA

    df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
    df["Mileage"] = pd.to_numeric(df["Mileage"], errors="coerce")
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")

    df["Make"] = df["Make"].astype("string")
    df["Model"] = df["Model"].astype("string")
    df["Trim"] = df["Trim"].astype("string")

    return df


def fmt_money(v):
    try:
        return f"${int(v):,}"
    except:
        return "—"


def fmt_km(v):
    try:
        return f"{int(v):,} km"
    except:
        return "—"


def make_pdf(summary_a, summary_b, label_a, label_b):
    """Generate a PDF comparing two models."""
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    y = height - 1 * inch

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(1 * inch, y, "Car Comparison Report")
    y -= 0.4 * inch

    pdf.setFont("Helvetica", 14)
    pdf.drawString(1 * inch, y, f"Model A: {label_a}")
    y -= 0.25 * inch
    pdf.drawString(1 * inch, y, f"Model B: {label_b}")
    y -= 0.5 * inch

    # Model A
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(1 * inch, y, f"Summary — {label_a}")
    y -= 0.25 * inch
    pdf.setFont("Helvetica", 11)
    for k, v in summary_a.items():
        pdf.drawString(1 * inch, y, f"{k}: {v}")
        y -= 0.20 * inch

    y -= 0.4 * inch

    # Model B
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(1 * inch, y, f"Summary — {label_b}")
    y -= 0.25 * inch
    pdf.setFont("Helvetica", 11)
    for k, v in summary_b.items():
        pdf.drawString(1 * inch, y, f"{k}: {v}")
        y -= 0.20 * inch

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()


# ======================================================
# LOAD DATA
# ======================================================
if not DB_PATH.exists():
    st.error("Database not found.")
    st.stop()

try:
    df = load_df(DB_PATH)
except Exception as e:
    st.error(f"Error loading data from DB: {e}")
    st.stop()

if df.empty:
    st.error("Database contains no data in Store table.")
    st.stop()


# ======================================================
# SIDEBAR — MODEL SELECTION
# ======================================================
with st.sidebar:
    st.header("Select Models to Compare")

    makes = sorted(df["Make"].dropna().unique())
    if not makes:
        st.error("No makes found in database.")
        st.stop()

    make_a = st.selectbox("Make A", makes)
    make_b = st.selectbox("Make B", makes)

    models_a = sorted(df[df["Make"] == make_a]["Model"].dropna().unique())
    models_b = sorted(df[df["Make"] == make_b]["Model"].dropna().unique())

    model_a = st.selectbox("Model A", models_a if len(models_a) else ["(none)"])
    model_b = st.selectbox("Model B", models_b if len(models_b) else ["(none)"])

    st.markdown("---")
    show_table = st.checkbox("Show Raw Tables", True)
    show_chart = st.checkbox("Show Price Chart", True)  # kept for future use if you add charts


# ======================================================
# FILTER SELECTED MODELS
# ======================================================
car_a = df[(df["Make"] == make_a) & (df["Model"] == model_a)]
car_b = df[(df["Make"] == make_b) & (df["Model"] == model_b)]

if car_a.empty or car_b.empty:
    st.warning("No cars found for the selected models.")
    st.stop()


# ======================================================
# SUMMARIES
# ======================================================
def model_summary(df_model):
    return {
        "Count": len(df_model),
        "Min Price": fmt_money(df_model["Price"].min()),
        "Max Price": fmt_money(df_model["Price"].max()),
        "Average Price": fmt_money(df_model["Price"].mean()),
        "Median Price": fmt_money(df_model["Price"].median()),
        "Average Mileage": fmt_km(df_model["Mileage"].mean()),
        "Year Range": f"{int(df_model['Year'].min())} - {int(df_model['Year'].max())}",
        "Common Fuel": df_model["Fuel"].mode()[0] if df_model["Fuel"].dropna().any() else "—",
        "Common Drivetrain": df_model["Drivetrain"].mode()[0] if df_model["Drivetrain"].dropna().any() else "—",
    }

sum_a = model_summary(car_a)
sum_b = model_summary(car_b)


# ======================================================
# DISPLAY SIDE-BY-SIDE
# ======================================================
st.subheader("📊 Summary Comparison")

c1, c2 = st.columns(2)

with c1:
    st.markdown(f"### **{make_a} {model_a}**")
    for k, v in sum_a.items():
        st.metric(k, v)

with c2:
    st.markdown(f"### **{make_b} {model_b}**")
    for k, v in sum_b.items():
        st.metric(k, v)


# ======================================================
# RAW TABLES
# ======================================================
if show_table:
    st.subheader(f"📄 Raw Data — {make_a} {model_a}")
    st.dataframe(car_a, use_container_width=True)

    st.subheader(f"📄 Raw Data — {make_b} {model_b}")
    st.dataframe(car_b, use_container_width=True)


# ======================================================
# EXPORT PDF — INSTANT DOWNLOAD
# ======================================================
st.markdown("---")
st.subheader("📤 Export as PDF")

label_a = f"{make_a} {model_a}"
label_b = f"{make_b} {model_b}"

if st.button("Generate & Download PDF"):
    pdf_bytes = make_pdf(sum_a, sum_b, label_a, label_b)

    st.download_button(
        label="⬇ Download PDF Report",
        data=pdf_bytes,
        file_name="car_comparison_report.pdf",
        mime="application/pdf"
    )

    st.success("PDF generated successfully!")
