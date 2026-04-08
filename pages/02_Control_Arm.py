import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 1. CONFIG & BRANDING ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div[data-testid="stMetricValue"] { color: #00235e; font-size: 32px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA LOADING & CLEANING ---
# IMPORTANT: Replace this with your Google Sheet URL for the Control Arm tab
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRNS4IPz-rmy9-KshbK9LaDDSnhpOi4QotEqUKUC8WcmVod0VwJPExr2TrIJK4kiRzYxTm2M6OArzr9/pub?gid=1638279052&single=true&output=csv"

def clean_currency(value):
    if pd.isna(value) or value == "": return 0.0
    s = str(value).replace('$', '').replace('%', '').replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    try: return float(s)
    except: return 0.0

@st.cache_data(ttl=60)
def load_and_parse():
    df_raw = pd.read_csv(SHEET_URL, header=None)
    
    # Weights - Row 1 and 2
    gross_w = clean_currency(df_raw.iloc[1, 1])
    net_w = clean_currency(df_raw.iloc[2, 1])
    
    # TMC - Rows 7 to 12
    tmc_df = df_raw.iloc[7:13, [0, 1, 2]]
    tmc_df.columns = ["MATERIALS", "COST($)", "PP SENSIVITY%"]
    
    # TTC - Rows 18 to 23 (6 processes)
    ttc_df = df_raw.iloc[18:24, 0:11] 
    ttc_df.columns = [
        "PROCESS", "CYCLE TIME", "HEADCOUNT", "DL RATE", 
        "TOTAL DL", "IL RATE", "OVERHEAD", "FC", "VC", "TOTAL RATE", "COST"
    ]
    
    # Logistics - Rows 26 to 28
    log_df = df_raw.iloc[26:29, [0, 1]]
    log_df.columns = ["ITEM", "COST"]

    return gross_w, net_w, tmc_df, ttc_df, log_df

try:
    g_w, n_w, tmc_raw, ttc_raw, log_raw = load_and_parse()
    
    # Cleaning numeric values
    tmc_raw["COST($)"] = tmc_raw["COST($)"].apply(clean_currency)
    rate_columns = ["DL RATE", "TOTAL DL", "IL RATE", "OVERHEAD", "FC", "VC", "TOTAL RATE", "COST"]
    for col in rate_columns:
        ttc_raw[col] = ttc_raw[col].apply(clean_currency)
    log_raw["COST"] = log_raw["COST"].apply(clean_currency)
    
except Exception as e:
    st.error(f"Error: {e}. Check if the Google Sheet matches the CSV structure.")
    st.stop()

# --- 3. HEADER ---
col_logo, col_title = st.columns([1, 4])
with col_logo:
    st.image("https://http2.mlstatic.com/D_NQ_NP_2X_855634-MLB75676618058_042024-F.webp", width=150)
    st.write(f"**Gross Weight:** {g_w} kg")
    st.write(f"**Net Weight:** {n_w} kg")

with col_title:
    st.title("⚙️ Lower Control Arm - WNP Simulator")
    st.caption("Assembly & Foundry Breakdown")

st.markdown("---")

# --- 4. SIDEBAR ---
st.sidebar.header("🕹️ Cost Drivers")

# Ball Joint Cost (Main driver in Row 7)
init_ball_joint = tmc_raw.iloc[0, 1]
ball_joint = st.sidebar.slider("Ball Joint Assy Cost ($)", 10.0, 30.0, float(init_ball_joint))

# Steel Scrap Sensitivity (Row 11)
init_steel = tmc_raw.iloc[4, 1]
steel_price_mod = st.sidebar.slider("Steel Scrap Variation (%)", -20, 50, 0)

st.sidebar.header("⚙️ Process Efficiency")
scrap_rate = st.sidebar.slider("Foundry Scrap (%)", 0.0, 10.0, 4.0)

st.sidebar.header("📈 Financials")
markup = st.sidebar.slider("Markup Multiplier", 1.0, 1.5, 1.17, step=0.01)

# --- 5. CALCULATIONS ---
tmc_dynamic = tmc_raw.copy()
tmc_dynamic.iloc[0, 1] = ball_joint # Update Ball Joint
tmc_dynamic.iloc[4, 1] = init_steel * (1 + (steel_price_mod/100)) # Update Steel
total_tmc = tmc_dynamic["COST($)"].sum()

base_ttc = ttc_raw["COST"].sum()
current_ttc = base_ttc * (1 + (scrap_rate/100))

total_log = log_raw["COST"].sum()
total_cost = total_tmc + current_ttc + total_log
wnp = total_cost * markup

# --- 6. DISPLAY ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total TMC", f"${total_tmc:.2f}")
m2.metric("Total TTC", f"${current_ttc:.2f}")
m3.metric("Logistics", f"${total_log:.2f}")
m4.metric("Total Cost", f"${total_cost:.2f}")

st.markdown("---")
st.subheader(f"Works Net Price (WNP): ${wnp:.2f}")

st.subheader("⚙️ Transformation Details")
st.dataframe(ttc_raw.style.format({c: "${:.2f}" for c in rate_columns}), use_container_width=True)

col_a, col_b = st.columns(2)
with col_a:
    st.subheader("📦 Material Breakdown")
    st.table(tmc_dynamic.style.format({"COST($)": "${:.2f}"}))
with col_b:
    st.subheader("🚚 Logistics")
    st.table(log_raw.style.format({"COST": "${:.2f}"}))

# Waterfall Chart
fig = go.Figure(go.Waterfall(
    x = ["TMC", "TTC", "Logistics", "Profit/Markup", "WNP"],
    y = [total_tmc, current_ttc, total_log, (wnp - total_cost), wnp],
    measure = ["relative", "relative", "relative", "relative", "total"]
))
st.plotly_chart(fig, use_container_width=True)
