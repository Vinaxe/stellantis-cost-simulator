import streamlit as st

st.set_page_config(page_title="Stellantis Cost Dashboard", layout="wide")

st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Stellantis.svg/960px-Stellantis.svg.png", width=200)

st.title("🚀 Global Purchasing & Engineering Cost Simulator")

st.markdown("""
### Project Overview
This dashboard provides real-time **Works Net Price (WNP)** simulations for Stellantis. 
Use the sidebar on the left to navigate between different vehicle components:

* **Cylinder Head:**
* **Suspension Control Arm:**  

**Key Objectives:**
1. Provide transparency into **TMC** and **TTC** breakdowns.
2. Simulate market volatility (Material prices).
3. Align engineering targets with purchasing markup strategies.
""")

st.info("👈 Select a component from the sidebar to begin the simulation.")
