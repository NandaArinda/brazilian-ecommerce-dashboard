import streamlit as st
import pandas as pd
import plotly.express as px

# ================================
# CONFIG
# ================================
st.set_page_config(page_title="E-Commerce Dashboard Brazil", layout="wide")

# ================================
# HEADER STORYTELLING
# ================================
st.markdown("""
# Brazilian E-Commerce Dashboard

## Business Understanding
Analisis ini bertujuan untuk memahami:
- Tren penjualan
- Perilaku customer
- Segmentasi pelanggan (RFM Analysis)
- Distribusi geografis pelanggan

---
""")

# ================================
# LOAD DATA
# ================================
@st.cache_data
def load_data():
    customers = pd.read_csv("olist_customers_dataset.csv")
    orders = pd.read_csv("olist_orders_dataset.csv")

    orders['order_purchase_timestamp'] = pd.to_datetime(
        orders['order_purchase_timestamp']
    )

    df = pd.merge(orders, customers, on="customer_id")
    return df

df = load_data()

# ================================
# SIDEBAR FILTER
# ================================
st.sidebar.header("Filter Data")

state_filter = st.sidebar.multiselect(
    "Pilih State",
    df['customer_state'].unique(),
    default=df['customer_state'].unique()
)

df = df[df['customer_state'].isin(state_filter)]

# ================================
# METRICS
# ================================
st.markdown("## Ringkasan Data")

col1, col2, col3 = st.columns(3)

col1.metric("Total Orders", df['order_id'].nunique())
col2.metric("Total Customers", df['customer_unique_id'].nunique())
col3.metric("Total City", df['customer_city'].nunique())

# ================================
# TREN BULANAN
# ================================
st.markdown("## Tren Order Bulanan")

df['month'] = df['order_purchase_timestamp'].dt.to_period('M').astype(str)

monthly_orders = df.groupby('month', as_index=False)['order_id'].nunique()

fig_month = px.line(
    monthly_orders,
    x='month',
    y='order_id',
    markers=True,
    title="Tren Order Bulanan"
)

st.plotly_chart(fig_month, use_container_width=True)

# ================================
# TREN HARIAN + MOVING AVERAGE
# ================================
st.markdown("## Tren Harian + Moving Average")

df['date'] = df['order_purchase_timestamp'].dt.floor('D')

daily_orders = df.groupby('date', as_index=False)['order_id'].nunique()

daily_orders['rolling_avg'] = daily_orders['order_id'].rolling(
    window=7,
    min_periods=1
).mean()

fig_daily = px.line(
    daily_orders,
    x='date',
    y=['order_id', 'rolling_avg'],
    title="Tren Harian + Moving Average"
)

st.plotly_chart(fig_daily, use_container_width=True)

# ================================
# TOP CITY & STATE
# ================================
st.markdown("## Top City & State")

col1, col2 = st.columns(2)

with col1:
    top_city = df['customer_city'].value_counts().head(10).reset_index()
    top_city.columns = ['city', 'count']

    fig_city = px.bar(top_city, x='count', y='city', orientation='h')
    st.plotly_chart(fig_city, use_container_width=True)

with col2:
    top_state = df['customer_state'].value_counts().head(10).reset_index()
    top_state.columns = ['state', 'count']

    fig_state = px.bar(top_state, x='count', y='state', orientation='h')
    st.plotly_chart(fig_state, use_container_width=True)

# ================================
# GEOSPATIAL ANALYSIS
# ================================
st.markdown("## Geospatial Analysis")

state_orders = df['customer_state'].value_counts().reset_index()
state_orders.columns = ['state', 'orders']

fig_geo = px.choropleth(
    state_orders,
    locations='state',
    locationmode='USA-states',
    color='orders',
    title="Distribusi Order per State"
)

st.plotly_chart(fig_geo, use_container_width=True)

st.info("""
 Insight:
- Order tidak merata antar state
- Beberapa state mendominasi transaksi
- Potensi ekspansi ada di wilayah dengan order rendah
""")

# ================================
# RFM ANALYSIS (WAJIB NILAI TINGGI)
# ================================
st.markdown("## RFM Customer Analysis")

snapshot_date = df['order_purchase_timestamp'].max()

rfm = df.groupby('customer_unique_id').agg({
    'order_purchase_timestamp': lambda x: (snapshot_date - x.max()).days,
    'order_id': 'nunique'
}).reset_index()

rfm.columns = ['customer_id', 'recency', 'frequency']

# scoring
rfm['R_score'] = pd.qcut(rfm['recency'], 4, labels=[4,3,2,1])
rfm['F_score'] = pd.qcut(rfm['frequency'].rank(method='first'), 4, labels=[1,2,3,4])

rfm['RFM_Score'] = rfm['R_score'].astype(str) + rfm['F_score'].astype(str)

# visual
fig_rfm = px.scatter(
    rfm,
    x='recency',
    y='frequency',
    size='frequency',
    title="RFM Segmentation"
)

st.plotly_chart(fig_rfm, use_container_width=True)

st.info("""
 Insight RFM:
- Customer loyal memiliki frequency tinggi & recency rendah
- Banyak customer hanya membeli sekali
- Strategi retensi sangat penting
""")

# ================================
# INSIGHT & CONCLUSION
# ================================
st.markdown("## Conclusion")

st.success("""
- Penjualan menunjukkan tren fluktuatif namun stabil
- Customer didominasi pembeli sekali transaksi
- Terdapat customer loyal yang bisa ditargetkan ulang
- Distribusi geografis tidak merata

 Rekomendasi:
- Fokus retensi customer
- Promo untuk repeat customer
- Ekspansi ke wilayah dengan demand rendah
""")

# ================================
# FOOTER
# ================================
st.markdown("---")
st.caption("Dashboard by Nanda Dwi Arinda")