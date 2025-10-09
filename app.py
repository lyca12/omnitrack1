# app/app.py

import streamlit as st
import pandas as pd
import sys
import os

# This is a crucial step to ensure the app can find the 'database' module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import DatabaseManager, AuthManager

# --- Page Configuration ---
st.set_page_config(
    page_title="OmniTrack",
    page_icon="🛒",
    layout="wide"
)

# --- Caching Database and Auth Managers ---
# This prevents re-initializing the database on every interaction
@st.cache_resource
def init_managers():
    """Initializes and returns the database and auth managers."""
    db = DatabaseManager()
    auth = AuthManager(db)
    return db, auth

db, auth = init_managers()

# --- Session State Initialization ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_info'] = None

# --- UI Components ---
st.title("🛒 OmniTrack — Unified Order & Inventory Platform")

# --- Login Interface ---
if not st.session_state['logged_in']:
    st.header("Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            user = auth.login(username, password)
            if user:
                st.session_state['logged_in'] = True
                st.session_state['user_info'] = user
                st.success("Login successful!")
                st.experimental_rerun()
            else:
                st.error("Invalid username or password.")
    
    st.info("""
    **Demo Accounts:**
    - **Username:** `admin` | **Password:** `admin`
    - **Username:** `customer` | **Password:** `customer`
    """)

# --- Main Application Interface (after login) ---
else:
    user = st.session_state['user_info']
    st.sidebar.header(f"Welcome, {user['username']}!")
    st.sidebar.caption(f"Role: {user['role'].capitalize()}")
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.session_state['user_info'] = None
        st.experimental_rerun()

    # --- Role-Based Dashboards ---
    if user['role'] == 'admin':
        st.header("Admin Dashboard")
        st.subheader("📦 All Products")
        
        try:
            products_df = db.get_all_products()
            st.dataframe(
                products_df,
                use_container_width=True,
                hide_index=True,
                column_config={"price": st.column_config.NumberColumn(format="$%.2f")}
            )
            
            # Low Stock Alerts
            low_stock_threshold = 10
            low_stock_products = products_df[products_df['stock_quantity'] <= low_stock_threshold]
            if not low_stock_products.empty:
                st.subheader("⚠️ Low Stock Alerts")
                st.dataframe(low_stock_products[['name', 'stock_quantity']], hide_index=True)

        except Exception as e:
            st.error(f"Failed to load products: {e}")

    elif user['role'] == 'customer':
        st.header("Customer Dashboard")
        st.subheader("🛍️ Shop for Products")
        
        try:
            products_df = db.get_all_products()
            st.dataframe(
                products_df[['name', 'category', 'price', 'stock_quantity']],
                use_container_width=True,
                hide_index=True,
                column_config={"price": st.column_config.NumberColumn(format="$%.2f")}
            )
        except Exception as e:
            st.error(f"Failed to load products: {e}")

