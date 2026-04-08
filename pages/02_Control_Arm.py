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
# IMPORTANT: Put your CONTROL ARM Google Sheet CSV link here!
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/YOUR_CONTROL_ARM_URL/pub?output=csv"

def clean_currency(value):
    if pd.isna(value) or value == "": return 0.0
    s = str(value).replace('$', '').replace('%', '').replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    try: return float(s)
    except: return 0.0

@st.cache_data(ttl=60)
def load_and_parse():
    # Reading the file (we simulate it locally, but you will use the URL)
    df_raw = pd.read_csv(SHEET_URL, header=None)
    
    # Weights (Rows 1 and 2)
    gross_w = clean_currency(df_raw.iloc[1, 1])
    net_w = clean_currency(df_raw.iloc[2, 1])
    
    # TMC - Control Arm starts on Row 6 and goes to 11
    tmc_df = df_raw.iloc[6:12, [0, 1, 2]]
    tmc_df.columns = ["MATERIALS", "COST($)", "PP SENSIVITY%"]
    
    # TTC - Control Arm processes start on Row 15 and go to 20
    ttc_df = df_raw.iloc[15:21, 0:11] 
    ttc_df.columns = [
        "PROCESS", "CYCLE TIME", "HEADCOUNT", "DL RATE", 
        "TOTAL DL", "IL RATE", "OVERHEAD", "FC", "VC", "TOTAL RATE", "COST"
    ]
    
    # Logistics - Control Arm logistics are on Rows 23 to 25
    log_df = df_raw.iloc[23:26, [0, 1]]
    log_df.columns = ["ITEM", "COST"]

    return gross_w, net_w, tmc_df, ttc_df, log_df

try:
    g_w, n_w, tmc_raw, ttc_raw, log_raw = load_and_parse()
    
    # Clean formatting
    tmc_raw["COST($)"] = tmc_raw["COST($)"].apply(clean_currency)
    
    rate_columns = ["DL RATE", "TOTAL DL", "IL RATE", "OVERHEAD", "FC", "VC", "TOTAL RATE", "COST"]
    for col in rate_columns:
        ttc_raw[col] = ttc_raw[col].apply(clean_currency)
        
    log_raw["COST"] = log_raw["COST"].apply(clean_currency)
except Exception as e:
    st.error("Connection Error: Please check the Control Arm Google Sheet URL.")
    st.stop()

# --- 3. HEADER & WEIGHT DATA ---
col_logo, col_title = st.columns([1, 4])
with col_logo:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Stellantis_logo.svg/1200px-Stellantis_logo.svg.png", width=150)
    st.write(f"**Gross Weight:** {g_w} kg")
    st.write(f"**Net Weight:** {n_w} kg")

with col_title:
    st.title("⚙️ Lower Control Arm - Works Net Price")
    st.caption("Strategic Cost Breakdown Analysis | Iron Casting & Assembly")

st.markdown("---")

# --- 4. SIDEBAR SIMULATION ---
st.sidebar.header("🕹️ Material Variables")

# The biggest cost is the Ball Joint. Let's make a slider for it.
initial_ball_joint = tmc_raw.iloc[0, 1] 
ball_joint_cost = st.sidebar.slider("Ball Joint Assembly ($)", 10.0, 25.0, float(initial_ball_joint))

# The second biggest metal cost is Steel Scrap. We use a multiplier.
steel_scrap_factor = st.sidebar.slider("Steel Scrap Price Inflation (%)", -20, 50, 0)

st.sidebar.header("⚙️ Operational Variables")
scrap_oee = st.sidebar.slider("Foundry Scrap / OEE Loss (%)", 0.0, 15.0, 5.0)
efficiency = st.sidebar.slider("Machining Optimization (%)", 0, 30, 0)

st.sidebar.header("📈 Financial Strategy")
markup_factor = st.sidebar.slider("Markup Factor (AC-DC/PROFIT)", 1.0, 2.0, 1.17, step=0.01)

# --- 5. DYNAMIC CALCULATION ---
# TMC Logic (Updating Ball Joint and Steel Scrap)
tmc_dynamic = tmc_raw.copy()
tmc_dynamic.iloc[0, 1] = ball_joint_cost # Update Ball Joint
tmc_dynamic.iloc[4, 1] = tmc_dynamic.iloc[4, 1] * (1 + (steel_scrap_factor/100)) # Update Steel Scrap

total_tmc = tmc_dynamic["COST($)"].sum()

# TTC Logic
base_ttc = ttc_raw["COST"].sum()
current_ttc = base_ttc * (1 + (scrap_oee/100)) * (1 - (efficiency/100))

# Logistics
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
st.subheader("⚙️ TTC Breakdown (Foundry & Machining Rates)")
ttc_formatting = {col: "${:.2f}" for col in ["DL RATE", "TOTAL DL", "IL RATE", "OVERHEAD", "FC", "VC", "TOTAL RATE", "COST"]}
st.dataframe(ttc_raw.style.format(ttc_formatting), use_container_width=True)

st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    st.subheader("📦 TMC Breakdown")
    st.table(tmc_dynamic.style.format({"COST($)": "${:.2f}"}))
    
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
