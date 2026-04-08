import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 1. CONFIG & BRANDING ---
st.set_page_config(page_title="Stellantis | T200 Cost Simulator", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div[data-testid="stMetricValue"] { color: #00235e; font-size: 32px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA LOADING & CLEANING ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRNS4IPz-rmy9-KshbK9LaDDSnhpOi4QotEqUKUC8WcmVod0VwJPExr2TrIJK4kiRzYxTm2M6OArzr9/pub?gid=1847821866&single=true&output=csv"

def clean_currency(value):
    if pd.isna(value) or value == "": return 0.0
    s = str(value).replace('$', '').replace('%', '').replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    try: return float(s)
    except: return 0.0

@st.cache_data(ttl=60)
def load_and_parse():
    df_raw = pd.read_csv(SHEET_URL, header=None)
    
    # Weights
    gross_w = clean_currency(df_raw.iloc[1, 1])
    net_w = clean_currency(df_raw.iloc[2, 1])
    
    # TMC
    tmc_df = df_raw.iloc[7:12, [0, 1, 2]]
    tmc_df.columns = ["MATERIALS", "COST($)", "PP SENSIVITY%"]
    
    # TTC - NOW GRABBING ALL 11 RATE COLUMNS
    ttc_df = df_raw.iloc[17:23, 0:11] 
    ttc_df.columns = [
        "PROCESS", "CYCLE TIME", "HEADCOUNT", "DL RATE", 
        "TOTAL DL", "IL RATE", "OVERHEAD", "FC", "VC", "TOTAL RATE", "COST"
    ]
    
    # Logistics
    log_df = df_raw.iloc[26:29, [0, 1]]
    log_df.columns = ["ITEM", "COST"]

    return gross_w, net_w, tmc_df, ttc_df, log_df

try:
    g_w, n_w, tmc_raw, ttc_raw, log_raw = load_and_parse()
    
    # Clean currency for Math and Display
    tmc_raw["COST($)"] = tmc_raw["COST($)"].apply(clean_currency)
    
    # Clean all the specific rate columns in TTC
    rate_columns = ["DL RATE", "TOTAL DL", "IL RATE", "OVERHEAD", "FC", "VC", "TOTAL RATE", "COST"]
    for col in rate_columns:
        ttc_raw[col] = ttc_raw[col].apply(clean_currency)
        
    log_raw["COST"] = log_raw["COST"].apply(clean_currency)
except:
    st.error("Connection Error: Check URL")
    st.stop()

# --- 3. HEADER & WEIGHT DATA ---
col_logo, col_title = st.columns([1, 4])
with col_logo:
    st.image("https://http2.mlstatic.com/D_NQ_NP_802214-MLB77654495713_072024-O-cabecote-do-motor-t-200-10-turbo-trs-cilindros-2022-2023.webp", width=150)
    st.write(f"**Gross Weight:** {g_w} kg")
    st.write(f"**Net Weight:** {n_w} kg")

with col_title:
    st.title("⚙️ T200 Cylinder Head - Works Net Price (WNP)")
    st.caption("Strategic Cost Breakdown Analysis")

st.markdown("---")

# --- 4. SIDEBAR SIMULATION ---
st.sidebar.header("🕹️ Production Variables")

initial_al_cost = tmc_raw.iloc[0, 1] 
initial_price_kg = initial_al_cost / g_w if g_w > 0 else 0.0

al_price_kg = st.sidebar.slider("Aluminum Price ($/kg)", 1.00, 6.00, initial_price_kg)
scrap_oee = st.sidebar.slider("Scrap Rate / OEE Loss (%)", 0.0, 15.0, 4.6)
efficiency = st.sidebar.slider("Process Optimization (%)", 0, 30, 0)

st.sidebar.header("📈 Financial Strategy")
markup_factor = st.sidebar.slider("Markup Factor (AC-DC/PROFIT)", 1.0, 2.0, 1.17, step=0.01)

# --- 5. DYNAMIC CALCULATION ---
current_al_cost = al_price_kg * g_w
others_tmc = tmc_raw.iloc[1:, 1].sum()
total_tmc = current_al_cost + others_tmc

base_ttc = ttc_raw["COST"].sum()
current_ttc = base_ttc * (1 + (scrap_oee/100)) * (1 - (efficiency/100))

total_log = log_raw["COST"].sum()

sum_total_cost = total_tmc + current_ttc + total_log
works_net = sum_total_cost * markup_factor

# --- 6. TOP METRICS ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total TMC", f"${total_tmc:.2f}")
m2.metric("Total TTC", f"${current_ttc:.2f}")
m3.metric("Logistics", f"${total_log:.2f}")
m4.metric("Total Cost", f"${sum_total_cost:.2f}")

st.markdown("---")
st.subheader(f"Works Net Price (WNP): ${works_net:.2f}")
st.caption(f"Calculation: Total Cost (${sum_total_cost:.2f}) x Markup Factor ({markup_factor})")

# --- 7. TABLES & WATERFALL ---
st.subheader("⚙️ TTC Breakdown (Transformation Rates)")
# Create a dictionary to format all 8 rate columns as currency automatically
ttc_formatting = {col: "${:.2f}" for col in ["DL RATE", "TOTAL DL", "IL RATE", "OVERHEAD", "FC", "VC", "TOTAL RATE", "COST"]}
# Use st.dataframe instead of st.table so you can scroll horizontally through all 11 columns
st.dataframe(ttc_raw.style.format(ttc_formatting), use_container_width=True)

st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    st.subheader("📦 TMC Breakdown")
    tmc_display = tmc_raw.copy()
    tmc_display.iloc[0, 1] = current_al_cost
    st.table(tmc_display.style.format({"COST($)": "${:.2f}"}))
    
    st.subheader("🚚 Logistics Breakdown")
    st.table(log_raw.style.format({"COST": "${:.2f}"}))

with col2:
    profit_value = works_net - sum_total_cost
    
    fig = go.Figure(go.Waterfall(
        orientation = "v",
        measure = ["relative", "relative", "relative", "relative", "total"],
        x = ["TMC", "TTC", "Logistics", "Markup (Profit)", "Works Net"],
        y = [total_tmc, current_ttc, total_log, profit_value, works_net],
        connector = {"line":{"color":"#00235e", "width": 2}},
        decreasing = {"marker":{"color":"#e74c3c"}},
        increasing = {"marker":{"color":"#2ecc71"}},
        totals = {"marker":{"color":"#00235e"}}
    ))
    st.plotly_chart(fig, use_container_width=True)
