import streamlit as st

st.set_page_config(page_title="Stellantis Cost Dashboard", layout="wide")

st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Stellantis_logo.svg/1200px-Stellantis_logo.svg.png", width=200)

st.title("🚀 Global Purchasing & Engineering Cost Simulator")

st.markdown("""
### Project Overview
This dashboard provides real-time **Works Net Price (WNP)** simulations for the T200 platform. 
Use the sidebar on the left to navigate between different vehicle components:

* **Cylinder Head:** GDC process analysis and Aluminum sensitivity.
* **Suspension Control Arm:** Forging/Stamping cost structures.

**Key Objectives:**
1. Provide transparency into **TMC** and **TTC** breakdowns.
2. Simulate market volatility (Material prices).
3. Align engineering targets with purchasing markup strategies.
""")

st.info("👈 Select a component from the sidebar to begin the simulation.")
