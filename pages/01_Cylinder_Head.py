import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 1. CONFIG ---
st.set_page_config(page_title="Stellantis | T200 Simulator", layout="wide")

# --- 2. DATA LOADING ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRNS4IPz-rmy9-KshbK9LaDDSnhpOi4QotEqUKUC8WcmVod0VwJPExr2TrIJK4kiRzYxTm2M6OArzr9/pub?gid=1847821866&single=true&output=csv"

def clean_currency(value):
    if pd.isna(value) or value == "": return 0.0
    s = str(value).replace('$', '').replace('%', '').replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    try: return float(s)
    except: return 0.0

@st.cache_data(ttl=60)
def load_data():
    df_raw = pd.read_csv(SHEET_URL, header=None)
    g_w = clean_currency(df_raw.iloc[1, 1])
    n_w = clean_currency(df_raw.iloc[2, 1])
    tmc_df = df_raw.iloc[7:12, [0, 1]].copy()
    tmc_df.columns = ["MATERIALS", "COST"]
    tmc_df["COST"] = tmc_df["COST"].apply(clean_currency)
    ttc_df = df_raw.iloc[17:23, 0:11].copy()
    ttc_df.columns = ["PROCESS", "CT", "HC", "DL_R", "T_DL", "IL_R", "OH", "FC", "VC", "T_RATE", "COST"]
    for col in ["CT", "T_RATE", "COST"]:
        ttc_df[col] = ttc_df[col].apply(clean_currency)
    log_df = df_raw.iloc[26:29, [0, 1]].copy()
    log_df.columns = ["ITEM", "COST"]
    log_df["COST"] = log_df["COST"].apply(clean_currency)
    return g_w, n_w, tmc_df, ttc_df, log_df

g_w, n_w, tmc_base, ttc_base, log_base = load_data()

# --- 3. HEADER WITH PART IMAGE ---
col_logo, col_text, col_part = st.columns([1, 2, 1])

with col_logo:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Stellantis.svg/960px-Stellantis.svg.png", width=120)

with col_text:
    st.title("⚙️ Cylinder Head T200")
    st.write(f"**Gross:** {g_w} kg | **Net:** {n_w} kg")
    st.caption("Bottom-Up Works Net Price Simulation")

with col_part:
    # This is the T200 Part Image
    st.image("https://http2.mlstatic.com/D_NQ_NP_2X_908493-MLB105796278454_022026-F.webp", caption="Part: T200 GDC Head", width=140)

st.divider()

# --- 4. SIDEBAR & LOGIC ---
st.sidebar.header("🕹️ Simulation")
al_price = st.sidebar.slider("Aluminum ($/kg)", 1.5, 5.0, 2.68)
scrap_rate = st.sidebar.slider("Scrap/OEE Impact (%)", 0.0, 15.0, 4.6)
markup = st.sidebar.slider("Markup Factor", 1.0, 1.5, 1.17, step=0.01)

# Sum Logic Fix
tmc_dyn = tmc_base.copy()
tmc_dyn.iloc[0, 1] = al_price * g_w 
total_tmc = tmc_dyn["COST"].sum()

ttc_dyn = ttc_base.copy()
ttc_dyn["COST"] = ttc_dyn["CT"] * ttc_dyn["T_RATE"] * (1 + (scrap_rate/100))
total_ttc = ttc_dyn["COST"].sum()

total_log = log_base["COST"].sum()
total_cost = total_tmc + total_ttc + total_log
wnp = total_cost * markup

# --- 5. TOP METRICS ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total TMC", f"${total_tmc:.2f}")
m2.metric("Total TTC", f"${total_ttc:.2f}")
m3.metric("Logistics", f"${total_log:.2f}")
m4.metric("Works Net Price", f"${wnp:.2f}")

st.subheader("Transformation Table")
st.dataframe(ttc_dyn.style.format({c: "${:.2f}" for c in ["T_RATE", "COST"]}), use_container_width=True)

c1, c2 = st.columns(2)
with c1:
    st.table(tmc_dyn.style.format({"COST": "${:.2f}"}))
with c2:
    st.table(log_base.style.format({"COST": "${:.2f}"}))
