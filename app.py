import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 1. CONFIG & BRANDING ---
st.set_page_config(page_title="Stellantis | T200 Cost Simulator", layout="wide")

# Stellantis Corporate Blue & Professional Styling
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div[data-testid="stMetricValue"] { color: #00235e; font-size: 32px; font-weight: bold; }
    .stTable { border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA LOADING & CLEANING ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRNS4IPz-rmy9-KshbK9LaDDSnhpOi4QotEqUKUC8WcmVod0VwJPExr2TrIJK4kiRzYxTm2M6OArzr9/pub?gid=1847821866&single=true&output=csv"

def clean_currency(value):
    """Converts strings like '$37,61' or '52,17%' to floats like 37.61 or 0.5217"""
    if pd.isna(value) or value == "": return 0.0
    s = str(value).replace('$', '').replace('%', '').replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    try:
        return float(s)
    except:
        return 0.0

@st.cache_data(ttl=60)
def load_and_parse():
    # In your case, we use the uploaded file logic for the live app
    df_raw = pd.read_csv(SHEET_URL, header=None)
    
    # Extracting Key Variables from your specific rows
    gross_weight = clean_currency(df_raw.iloc[1, 1])
    
    # 1. TMC Table (Rows 7 to 11)
    tmc_df = df_raw.iloc[7:12, [0, 1, 2]]
    tmc_df.columns = ["MATERIALS", "COST($)", "PP SENSIVITY%"]
    
    # 2. TTC Table (Rows 17 to 22)
    ttc_df = df_raw.iloc[17:23, [0, 1, 10]] # Process, Cycle Time, Cost
    ttc_df.columns = ["PROCESS", "CYCLE TIME", "COST"]
    
    # 3. Logistics (Rows 26 to 28)
    log_df = df_raw.iloc[26:29, [0, 1]]
    log_df.columns = ["ÍTEM", "COST"]

    return gross_weight, tmc_df, ttc_df, log_df

try:
    g_weight, tmc_raw, ttc_raw, log_raw = load_and_parse()
    # Convert numeric columns for calculation
    tmc_raw["COST($)"] = tmc_raw["COST($)"].apply(clean_currency)
    ttc_raw["COST"] = ttc_raw["COST"].apply(clean_currency)
    log_raw["COST"] = log_raw["COST"].apply(clean_currency)
except:
    st.error("Connection Error: Please check the Google Sheet URL.")
    st.stop()

# --- 3. HEADER ---
col_logo, col_title = st.columns([1, 4])
with col_logo:
    # Placeholder for Stellantis Logo
    st.image("https://http2.mlstatic.com/D_NQ_NP_2X_908493-MLB105796278454_022026-F.webp", width=150)
with col_title:
    st.title("⚙️ T200 Cylinder Head - Works Net Price (WNP)")
    st.caption("Strategic Cost Breakdown Analysis | R&D Engineering & Purchasing")

st.markdown("---")

# --- 4. SIDEBAR SIMULATION ---
st.sidebar.header("🕹️ Market Variables")
al_price = st.sidebar.slider("Aluminum Market Price ($/kg)", 1.50, 5.00, 2.48)
scrap = st.sidebar.slider("Process Scrap Rate (%)", 0.0, 10.0, 4.6)

st.sidebar.header("⚙️ Operational Efficiency")
efficiency = st.sidebar.slider("TTC Optimization (%)", 0, 30, 0)

st.sidebar.header("📈 Financial Strategy")
markup_slider = st.sidebar.slider("Markup / Profit ($)", 0.0, 20.0, 10.47)
st.sidebar.caption("AC-DC / PROFIT Strategy")

# --- 5. DYNAMIC CALCULATION ---
# TMC Logic (Adjusting based on Al Price slider)
# Your sheet uses $37,61 for 2.48 $/kg. We scale it.
aluminum_cost_base = tmc_raw.iloc[0, 1] 
others_tmc = tmc_raw.iloc[1:, 1].sum()
current_tmc = (aluminum_cost_base / 2.48 * al_price) * (1 + (scrap/100) - 0.046) + others_tmc

# TTC Logic
current_ttc = ttc_raw["COST"].sum() * (1 - (efficiency/100))

# Logistics
current_log = log_raw["COST"].sum()

# Final Price
final_wnp = current_tmc + current_ttc + current_log + markup_slider

# --- 6. TOP METRIC ---
st.metric("Works Net Price (WNP)", f"${final_wnp:.2f}", delta=f"${final_wnp - 72.09:.2f} vs Target")

# --- 7. TABLES ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📦 Total Material Cost (TMC)")
    st.table(tmc_raw.style.format({"COST($)": "${:.2f}"}))
    
    st.subheader("⚙️ Transformation Cost (TTC)")
    st.table(ttc_raw.style.format({"COST": "${:.2f}"}))

with col2:
    st.subheader("🚚 Logistics & Packaging")
    st.table(log_raw.style.format({"COST": "${:.2f}"}))
    
    # --- WATERFALL CHART ---
    st.subheader("💡 Strategic Build-up")
    fig = go.Figure(go.Waterfall(
        orientation = "v",
        measure = ["relative", "relative", "relative", "relative", "total"],
        x = ["TMC", "TTC", "Logistics", "Markup", "Works Net"],
        y = [current_tmc, current_ttc, current_log, markup_slider, final_wnp],
        connector = {"line":{"color":"#00235e", "width": 2}},
        decreasing = {"marker":{"color":"#e74c3c"}},
        increasing = {"marker":{"color":"#2ecc71"}},
        totals = {"marker":{"color":"#00235e"}}
    ))
    fig.update_layout(height=400, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)
