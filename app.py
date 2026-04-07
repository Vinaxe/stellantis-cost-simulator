# stlite: requirements = ["plotly", "pandas"]

import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Stellantis CBD", layout="wide")
st.title("⚙️ T200 Cylinder Head - Offline Test")

st.subheader("1. Production Variables")
col1, col2, col3 = st.columns(3)
with col1:
    aluminum_price = st.slider("Aluminum Price ($/kg)", 2.00, 5.00, 2.48)
with col2:
    efficiency_gain = st.slider("Cycle Time Optimization (%)", 0, 30, 0)

st.success("✅ The dashboard interface is working perfectly!")

df_fake = pd.DataFrame({
    "Category": ["Material", "Melting", "Machining"],
    "Value ($)": [50.0, 15.0, 35.0]
})

fig = px.pie(df_fake, values="Value ($)", names="Category", hole=0.4)
st.plotly_chart(fig, use_container_width=True)
