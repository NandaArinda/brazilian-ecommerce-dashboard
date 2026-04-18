import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# ================================
# PAGE CONFIG
# ================================
st.set_page_config(page_title="E-Commerce Dashboard Brazil", layout="wide")

# ================================
# MODERN UI STYLE
# ================================
st.markdown("""
<style>
    .main {
        background-color: #0f172a;
        color: white;
    }

    .block-container {
        padding-top: 2rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }

    h1, h2, h3 {
        color: #ffffff;
    }

    div[data-testid="metric-container"] {
        background-color: #1e293b;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# ================================
# HEADER
# ================================
st.title(" E-Commerce Analytics Dashboard")
st.caption("Brazil Olist Dataset | Interactive Business Intelligence Dashboard")

st.markdown("---")

# ================================
# LOAD DATA
# ================================
@st.cache_data
def load_data():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    path1 = os.path.join(BASE_DIR, "data/main_data.csv")
    path2 = os.path.join(BASE_DIR, "../data/main_data.csv")

    file_path = path1 if os.path.exists(path1) else path2

    df = pd.read_csv(file_path)
    df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
    
    return df

df = load_data()

# ================================
# SIDEBAR FILTER (UPDATED 🔥)
# ================================
st.sidebar.header(" Filter Data")

min_date = df['order_purchase_timestamp'].min().date()
max_date = df['order_purchase_timestamp'].max().date()

date_range = st.sidebar.date_input(
    "Rentang Tanggal",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    key="date_filter"
)

# 🔥 TAMBAHAN ALL STATE
state_options = sorted(df['customer_state'].dropna().unique())
state_options_with_all = ["All State"] + state_options

state_filter = st.sidebar.multiselect(
    "Filter State",
    options=state_options_with_all,
    default=["All State"],
    key="state_filter"
)

# ================================
# FILTER ENGINE (UPDATED 🔥)
# ================================
filtered_df = df.copy()

# filter tanggal
if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = filtered_df[
        (filtered_df['order_purchase_timestamp'].dt.date >= start_date) &
        (filtered_df['order_purchase_timestamp'].dt.date <= end_date)
    ]

# 🔥 LOGIC ALL STATE
if "All State" not in state_filter:
    filtered_df = filtered_df[
        filtered_df['customer_state'].isin(state_filter)
    ]

# safety check
if filtered_df.empty:
    st.warning("Data kosong untuk filter yang dipilih.")
    st.stop()

st.caption(" Real-time dashboard update aktif")

st.markdown("---")

# ================================
# KPI METRICS
# ================================
st.subheader(" Key Performance Indicator")

col1, col2, col3 = st.columns(3)

col1.metric(" Total Orders", f"{filtered_df['order_id'].nunique():,}")
col2.metric(" Total Customers", f"{filtered_df['customer_unique_id'].nunique():,}")
col3.metric(" Total Cities", f"{filtered_df['customer_city'].nunique():,}")

st.markdown("---")

# ================================
# TREND ORDER
# ================================
st.subheader(" Order Trend Analysis")

filtered_df['month'] = filtered_df['order_purchase_timestamp'].dt.to_period('M').astype(str)

monthly_orders = filtered_df.groupby('month', as_index=False)['order_id'].nunique()
monthly_orders.columns = ['Bulan', 'Jumlah Order']

peak = monthly_orders.loc[monthly_orders['Jumlah Order'].idxmax()]

fig1 = go.Figure()
fig1.add_trace(go.Scatter(
    x=monthly_orders['Bulan'],
    y=monthly_orders['Jumlah Order'],
    mode='lines+markers',
    name='Orders'
))

fig1.add_trace(go.Scatter(
    x=[peak['Bulan']],
    y=[peak['Jumlah Order']],
    mode='markers+text',
    marker=dict(color='red', size=12),
    text=["Puncak"],
    textposition="top center"
))

col1, col2 = st.columns(2)

with col1:
    st.plotly_chart(fig1, use_container_width=True, key="chart_month")

with col2:
    st.info(f"""
    - Peak Month: **{peak['Bulan']}**
    - Total Orders: **{peak['Jumlah Order']}**
    """)

st.markdown("---")

# ================================
# TOP CITY
# ================================
st.subheader(" Top 10 Cities (2017–2018)")

filtered_df['year'] = filtered_df['order_purchase_timestamp'].dt.year
df_city = filtered_df[filtered_df['year'].isin([2017, 2018])]

top_city = df_city['customer_city'].value_counts().head(10).reset_index()
top_city.columns = ['Kota', 'Jumlah Customer']

total_customer = df_city['customer_unique_id'].nunique()

top_city['Persentase'] = (top_city['Jumlah Customer'] / total_customer * 100).round(2)
top_city = top_city.sort_values('Jumlah Customer')

top1 = top_city.iloc[-1]

fig2 = go.Figure(go.Bar(
    x=top_city['Jumlah Customer'],
    y=top_city['Kota'],
    orientation='h',
    text=top_city['Persentase'].astype(str) + "%",
    textposition="inside"
))

col1, col2 = st.columns(2)

with col1:
    st.plotly_chart(fig2, use_container_width=True, key="chart_city")

with col2:
    st.info(f"""
    - Top city: **{top1['Kota']}**
    """)

st.markdown("---")

# ================================
# RFM ANALYSIS
# ================================
st.subheader(" Customer Segmentation (RFM)")

snapshot = filtered_df['order_purchase_timestamp'].max()

rfm = filtered_df.groupby('customer_unique_id').agg(
    recency=('order_purchase_timestamp', lambda x: (snapshot - x.max()).days),
    frequency=('order_id', 'nunique')
).reset_index()

rfm['R_score'] = pd.qcut(rfm['recency'], 4, labels=[4, 3, 2, 1])
rfm['F_score'] = pd.qcut(rfm['frequency'].rank(method='first'), 4, labels=[1, 2, 3, 4])
rfm['RFM_Score'] = rfm['R_score'].astype(str) + rfm['F_score'].astype(str)

fig3 = px.scatter(
    rfm,
    x='recency',
    y='frequency',
    size='frequency',
    color='RFM_Score',
    title="RFM Segmentation"
)

st.plotly_chart(fig3, use_container_width=True, key="chart_rfm")

st.markdown("---")

st.caption("Dashboard by Nanda Dwi Arinda | Olist Dataset")
