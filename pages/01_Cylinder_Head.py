import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 1. CONFIG ---
st.set_page_config(page_title="Stellantis | T200 Simulator", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div[data-testid="stMetricValue"] { color: #00235e; font-size: 32px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA LOADING ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRNS4IPz-rmy9-KshbK9LaDDSnhpOi4QotEqUKUC8WcmVod0VwJPExr2TrIJK4kiRzYxTm2M6OArzr9/pub?gid=1847821866&single=true&output=csv"

def clean_currency(value):
    if pd.isna(value) or value == "": return 0.0
    s = str(value).replace('$', '').replace('%', '').replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    try: return float(s)
    except: return 0.0

@st.cache_data(ttl=60)
def load_t200_data():
    df_raw = pd.read_csv(SHEET_URL, header=None)
    g_w = clean_currency(df_raw.iloc[1, 1])
    n_w = clean_currency(df_raw.iloc[2, 1])
    
    # TMC (Rows 7 to 11)
    tmc_df = df_raw.iloc[7:12, [0, 1]].copy()
    tmc_df.columns = ["MATERIALS", "COST"]
    tmc_df["COST"] = tmc_df["COST"].apply(clean_currency)
    
    # TTC (Rows 17 to 22)
    ttc_df = df_raw.iloc[17:23, 0:11].copy()
    ttc_df.columns = ["PROCESS", "CT", "HC", "DL_R", "T_DL", "IL_R", "OH", "FC", "VC", "T_RATE", "COST"]
    for col in ["CT", "T_RATE", "COST"]:
        ttc_df[col] = ttc_df[col].apply(clean_currency)
    
    # Logistics (Rows 26 to 28)
    log_df = df_raw.iloc[26:29, [0, 1]].copy()
    log_df.columns = ["ITEM", "COST"]
    log_df["COST"] = log_df["COST"].apply(clean_currency)
    
    return g_w, n_w, tmc_df, ttc_df, log_df

g_w, n_w, tmc_base, ttc_base, log_base = load_t200_data()

# --- 3. HEADER WITH PART PHOTO ---
col_logo, col_title, col_img = st.columns([1, 3, 1])
with col_logo:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Stellantis.svg/960px-Stellantis.svg.png", width=120)
with col_title:
    st.title("⚙️ T200 Cylinder Head - WNP")
    st.write(f"**Gross Weight:** {g_w} kg | **Net Weight:** {n_w} kg")
with col_img:
    st.image("https://http2.mlstatic.com/D_NQ_NP_2X_802214-MLB77654495713_072024-F.webp", width=130, caption="T200 Part")

st.markdown("---")

# --- 4. SIDEBAR ---
st.sidebar.header("🕹️ Parameters")
al_price = st.sidebar.slider("Aluminum ($/kg)", 1.0, 6.0, 1.79) # Default based on $37.61/21kg
scrap_oee = st.sidebar.slider("Scrap/OEE Impact (%)", 0.0, 15.0, 0.00)
markup = st.sidebar.slider("Markup Factor", 1.0, 2.0, 1.17, step=0.01)

# --- 5. DYNAMIC CALCULATION (Bottom-Up Sum) ---
# A. TMC Table Update
tmc_dyn = tmc_base.copy()
tmc_dyn.iloc[0, 1] = al_price * g_w  # Update Aluminum Row
total_tmc = tmc_dyn["COST"].sum()    # SUM THE UPDATED TABLE

# B. TTC Table Update
ttc_dyn = ttc_base.copy()
# Every row cost is updated by scrap
ttc_dyn["COST"] = ttc_dyn["COST"] * (1 + (scrap_oee/100))
total_ttc = ttc_dyn["COST"].sum()    # SUM THE UPDATED TABLE

# C. Logistics & WNP
total_log = log_base["COST"].sum()
total_cost = total_tmc + total_ttc + total_log
wnp = total_cost * markup

# --- 6. DISPLAY ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total TMC (Sum)", f"${total_tmc:.2f}")
m2.metric("Total TTC (Sum)", f"${total_ttc:.2f}")
m3.metric("Logistics", f"${total_log:.2f}")
m4.metric("Works Net Price", f"${wnp:.2f}")

st.subheader("⚙️ Transformation Cost Breakdown")
st.dataframe(ttc_dyn.style.format({c: "${:.2f}" for c in ["T_RATE", "COST"]}), use_container_width=True)

c1, c2 = st.columns(2)
with c1:
    st.subheader("📦 Materials")
    st.table(tmc_dyn.style.format({"COST": "${:.2f}"}))
with c2:
    st.subheader("🚚 Logistics")
    st.table(log_base.style.format({"COST": "${:.2f}"}))
