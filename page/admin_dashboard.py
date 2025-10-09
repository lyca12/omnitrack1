# pages/1_Admin_Dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
from database import DatabaseManager
from models import OrderStatus

st.set_page_config(page_title="Admin Dashboard", layout="wide")
st.title("📊 Admin Dashboard")

# --- Authentication Check ---
if "user_info" not in st.session_state or st.session_state.user_info is None:
    st.warning("You must be logged in to view this page.")
    st.stop()
if st.session_state.user_info.role != 'admin':
    st.error("You must be an admin to view this page.")
    st.stop()

# --- App Logic ---
@st.cache_resource
def get_db():
    return DatabaseManager()
db = get_db()

products = db.get_all_products()
orders = db.get_all_orders()

# Key Metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Products", len(products))
col2.metric("Total Orders", len(orders))

delivered_orders = [o for o in orders if o.status == OrderStatus.DELIVERED]
total_revenue = sum(o.total_amount for o in delivered_orders)
col3.metric("Total Revenue", f"${total_revenue:,.2f}")

pending_orders = [o for o in orders if o.status in [OrderStatus.PLACED, OrderStatus.PAID]]
col4.metric("Pending Orders", len(pending_orders))
st.divider()

# Charts
col1, col2 = st.columns(2)
with col1:
    if orders:
        status_counts = pd.Series([o.status.value for o in orders]).value_counts()
        fig = px.pie(status_counts, values=status_counts.values, names=status_counts.index, title="Order Status Distribution")
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("⚠️ Low Stock Alerts")
    low_stock_products = [p for p in products if p.is_low_stock]
    if low_stock_products:
        df_low_stock = pd.DataFrame([{"Name": p.name, "Stock": p.stock_quantity} for p in low_stock_products])
        st.dataframe(df_low_stock, use_container_width=True, hide_index=True)
    else:
        st.success("All products are well-stocked!")
