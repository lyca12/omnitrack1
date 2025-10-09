# Home.py
import streamlit as st
from database import DatabaseManager, AuthManager

st.set_page_config(page_title="OmniTrack", page_icon="🛒", layout="centered")

@st.cache_resource
def init_managers():
    db = DatabaseManager()
    auth = AuthManager(db)
    return db, auth

db, auth = init_managers()

# Initialize session state
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "cart" not in st.session_state:
    st.session_state.cart = {} # Using session state for cart is simpler for Streamlit

st.title("🛒 OmniTrack — Unified Platform")

# Show login form or welcome message
if not st.session_state.user_info:
    st.header("Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", type="primary")

        if submitted:
            user = auth.login(username, password)
            if user:
                st.session_state.user_info = user
                st.rerun()
            else:
                st.error("Invalid username or password")
    
    st.info("""
    **Demo Accounts:**
    - **Username:** `admin` | **Password:** `admin`
    - **Username:** `staff` | **Password:** `staff`
    - **Username:** `customer` | **Password:** `customer`
    """)
else:
    user = st.session_state.user_info
    st.header(f"Welcome, {user.username}!")
    st.write(f"Your role: **{user.role.value.capitalize()}**")
    st.info("Select a page from the sidebar to get started.")

    if st.button("Logout"):
        st.session_state.user_info = None
        st.session_state.cart = {} # Clear cart on logout
        st.rerun()
