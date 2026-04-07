import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. LIVE CONNECTION (Replace with your CSV URL)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRNS4IPz-rmy9-KshbK9LaDDSnhpOi4QotEqUKUC8WcmVod0VwJPExr2TrIJK4kiRzYxTm2M6OArzr9/pubhtml?gid=827336911&single=true"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        return df
    except:
        # Fallback dummy data for testing
        return pd.DataFrame({
            "Component": ["Aluminium", "Melting", "GDC", "Logistics"],
            "Cost": [50.0, 10.0, 15.0, 5.0],
            "Category": ["TMC", "TTC", "TTC", "Logistics"]
        })

df = load_data()

# 2. PAGE CONFIG & STELLANTIS BRANDING
st.set_page_config(page_title="Stellantis WNP Simulator", layout="wide")

# CSS to inject professional styling and background
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border-left: 5px solid #00235e; }
    </style>
    """, unsafe_allow_html=True)

# 3. HEADER: TITLE & IMAGE
col_t1, col_t2 = st.columns([3, 1])
with col_t1:
    st.title("🚗 Works Net Price Simulator")
    st.subheader("Project: Cylinder Head T200")
with col_t2:
    # Replace this URL with a real link to your T200 image
    st.image("https://http2.mlstatic.com/D_Q_NP_2X_781277-MLB106116088816_022026-R.webp/150", caption="T200 Component", width=150)

st.markdown("---")

# 4. SIDEBAR: THE CONTROLS
st.sidebar.header("🕹️ Production Variables")
al_price = st.sidebar.slider("Aluminum ($/kg)", 2.0, 5.0, 2.48)
efficiency = st.sidebar.slider("TTC Optimization (%)", 0, 30, 0)
scrap = st.sidebar.slider("Scrap Rate (%)", 1.0, 10.0, 4.6)

st.sidebar.markdown("---")
st.sidebar.header("📈 Financial Strategy")
markup = st.sidebar.slider("Markup ($)", 0.0, 20.0, 10.47)
st.sidebar.caption("AC-DC / PROFIT")

# 5. CALCULATIONS
# Logic: We filter the Google Sheet by "Category" to make the tables
tmc_base = df[df['Category'] == 'TMC']['Cost'].sum() if 'Category' in df.columns else 45.20
ttc_base = df[df['Category'] == 'TTC']['Cost'].sum() if 'Category' in df.columns else 8.84
logistics_base = df[df['Category'] == 'Logistics']['Cost'].sum() if 'Category' in df.columns else 0.67

# Dynamic Adjustments
current_tmc = (tmc_base / 2.48) * al_price * (1 + (scrap/100) - 0.046) 
current_ttc = ttc_base * (1 - (efficiency/100))
works_net = current_tmc + current_ttc + logistics_base + markup

# 6. TOP METRIC
st.metric(label="Works Net Price (WNP)", value=f"${works_net:.2f}", delta=f"${works_net - (tmc_base+ttc_base+logistics_base+10.47):.2f} vs Baseline")

# 7. PROFESSIONAL TABLES
st.markdown("### 📊 Cost Breakdown Tables")
col_tab1, col_tab2 = st.columns(2)

with col_tab1:
    st.write("**Total Material Cost (TMC)**")
    # Professional Styling for Table
    tmc_df = df[df['Category'] == 'TMC'] if 'Category' in df.columns else df.head(2)
    st.table(tmc_df)

    st.write("**Total Transformation Cost (TTC)**")
    ttc_df = df[df['Category'] == 'TTC'] if 'Category' in df.columns else df.tail(2)
    st.table(ttc_df)

with col_tab2:
    st.write("**Logistics Cost**")
    log_df = df[df['Category'] == 'Logistics'] if 'Category' in df.columns else df.iloc[[0]]
    st.table(log_df)
    
    st.write("**Financial Markup**")
    st.info(f"Target Markup (AC-DC/PROFIT): **${markup:.2f}**")

# 8. PROFESSIONAL WATERFALL
st.markdown("---")
st.subheader("💡 Strategic Build-up Analysis")

fig = go.Figure(go.Waterfall(
    name = "WNP", orientation = "v",
    measure = ["relative", "relative", "relative", "relative", "total"],
    x = ["TMC", "TTC", "Logistics", "Markup", "Works Net"],
    textposition = "outside",
    text = [f"${current_tmc:.2f}", f"${current_ttc:.2f}", f"${logistics_base:.2f}", f"${markup:.2f}", f"Total: ${works_net:.2f}"],
    y = [current_tmc, current_ttc, logistics_base, markup, works_net],
    connector = {"line":{"color":"#00235e", "width": 2}},
    decreasing = {"marker":{"color":"#e74c3c"}},
    increasing = {"marker":{"color":"#2ecc71"}},
    totals = {"marker":{"color":"#00235e"}}
))

fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
st.plotly_chart(fig, use_container_width=True)
