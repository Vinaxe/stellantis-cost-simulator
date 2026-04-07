import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. LIVE CONNECTION
# Ensure you use the "Publish to Web" -> "CSV" link from Google Sheets
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRNS4IPz-rmy9-KshbK9LaDDSnhpOi4QotEqUKUC8WcmVod0VwJPExr2TrIJK4kiRzYxTm2M6OArzr9/pubhtml?gid=827336911&single=true"

@st.cache_data(ttl=60) # Refreshes data every minute
def load_data():
    try:
        return pd.read_csv(SHEET_URL)
    except:
        # Fallback if URL is not set yet
        return pd.DataFrame({"Category": ["Material", "Process", "Logistics"], "Value": [10, 5, 2]})

df = load_data()

# 2. APP LAYOUT
st.set_page_config(page_title="Stellantis CBD Simulator", layout="wide")
st.title("📊 T200 Cylinder Head - Live Cost Simulator")

# 3. INTERACTIVE SLIDERS
st.sidebar.header("🕹️ Production Variables")
aluminum_price = st.sidebar.slider("Aluminum Price ($/kg)", 2.0, 5.0, 2.48)
efficiency_gain = st.sidebar.slider("Process Optimization (%)", 0, 30, 0)
scrap_rate = st.sidebar.slider("Scrap Rate (%)", 1.0, 10.0, 4.6)

# 4. CALCULATION LOGIC (Connecting Sliders to Data)
# We assume the first row of your sheet is 'Material'
gross_weight = 21.0
current_material_cost = (gross_weight * aluminum_price) * (1 + (scrap_rate/100))

# We assume other rows are process steps
# This logic reduces the process costs based on the 'efficiency' slider
base_process_cost = 8.84 
optimized_process_cost = base_process_cost * (1 - (efficiency_gain/100))
logistics = 10.47

total_price = current_material_cost + optimized_process_cost + logistics

# 5. WATERFALL CHART (The Professional Choice)
fig = go.Figure(go.Waterfall(
    name = "CBD", orientation = "v",
    measure = ["relative", "relative", "relative", "total"],
    x = ["Material", "Transformation", "Logistics/Margin", "Final Price"],
    textposition = "outside",
    text = [f"${current_material_cost:.2f}", f"${optimized_process_cost:.2f}", f"${logistics:.2f}", f"${total_price:.2f}"],
    y = [current_material_cost, optimized_process_cost, logistics, total_price],
    connector = {"line":{"color":"rgb(63, 63, 63)"}},
))

fig.update_layout(title = "Cost Build-up (Waterfall Analysis)", showlegend = False)

# 6. DISPLAY
col1, col2 = st.columns([1, 2])
with col1:
    st.metric("Final Piece Price", f"${total_price:.2f}", f"{-efficiency_gain}% Process Cost")
    st.dataframe(df) # Shows your raw Google Sheet data
with col2:
    st.plotly_chart(fig, use_container_width=True)
