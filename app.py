import streamlit as st
import pandas as pd

st.set_page_config(page_title="Hello Streamlit", page_icon="👋", layout="centered")

st.title("Hello, Streamlit in Codespaces 👋")
st.write("This is a simple demo running entirely in your browser-based dev environment.")

name = st.text_input("Your name", "Hawkar")
temps = pd.DataFrame({"Temperature (°F)": [70, 75, 80], "Humidity (%)": [30, 45, 50]})

st.subheader(f"Welcome, {name}!")
st.dataframe(temps)

st.line_chart(temps["Temperature (°F)"])

if st.button("Compute Average Temp"):
    avg = temps["Temperature (°F)"].mean()
    st.success(f"Average temperature is {avg:.1f}°F")