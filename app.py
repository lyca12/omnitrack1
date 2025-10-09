import streamlit as st
from auth import AuthManager
from database import DatabaseManager
import pandas as pd

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'username' not in st.session_state:
    st.session_state.username = None

# Initialize database and auth
@st.cache_resource
def init_managers():
    db = DatabaseManager()
    auth = AuthManager(db)
    return db, auth

db, auth = init_managers()

def main():
    st.set_page_config(
        page_title="OmniTrack - Order & Inventory Management",
        page_icon="📦",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    if not st.session_state.authenticated:
        show_login_page()
    else:
        show_authenticated_app()

def show_login_page():
    st.title("🏪 OmniTrack")
    st.subheader("Order & Inventory Management Platform")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2, tab3 = st.tabs(["Login", "Sign Up", "Demo Access"])
        
        with tab1:
            st.header("Login")
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Login", type="primary"):
                user = auth.authenticate_user(username, password)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user_role = user['role']
                    st.session_state.username = username
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        
        with tab2:
            st.header("Sign Up")
            new_username = st.text_input("Username", key="signup_username")
            new_password = st.text_input("Password", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
            
            if st.button("Sign Up", type="primary"):
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters long")
                else:
                    if auth.register_user(new_username, new_password, 'customer'):
                        st.success("Account created successfully! Please login.")
                    else:
                        st.error("Username already exists")
        
        with tab3:
            st.header("Demo Access")
            st.write("Try OmniTrack with demo accounts:")
            
            col_demo1, col_demo2, col_demo3 = st.columns(3)
            
            with col_demo1:
                if st.button("Admin Demo", type="secondary", use_container_width=True):
                    st.session_state.authenticated = True
                    st.session_state.user_role = 'admin'
                    st.session_state.username = 'admin_demo'
                    st.rerun()
            
            with col_demo2:
                if st.button("Staff Demo", type="secondary", use_container_width=True):
                    st.session_state.authenticated = True
                    st.session_state.user_role = 'staff'
                    st.session_state.username = 'staff_demo'
                    st.rerun()
            
            with col_demo3:
                if st.button("Customer Demo", type="secondary", use_container_width=True):
                    st.session_state.authenticated = True
                    st.session_state.user_role = 'customer'
                    st.session_state.username = 'customer_demo'
                    st.rerun()

def show_authenticated_app():
    # Sidebar navigation
    st.sidebar.title(f"Welcome, {st.session_state.username}")
    st.sidebar.write(f"Role: {st.session_state.user_role.title()}")
    
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.user_role = None
        st.session_state.username = None
        st.rerun()
    
    st.sidebar.divider()
    
    # Role-based navigation
    if st.session_state.user_role == 'admin':
        show_admin_navigation()
    elif st.session_state.user_role == 'staff':
        show_staff_navigation()
    else:  # customer
        show_customer_navigation()

def show_admin_navigation():
    st.sidebar.header("Admin Panel")
    
    pages = {
        "Dashboard": "admin_dashboard",
        "Product Management": "product_management",
        "Order Management": "order_management",
        "Reports": "reports"
    }
    
    selected_page = st.sidebar.radio("Navigation", list(pages.keys()))
    
    if selected_page == "Dashboard":
        show_admin_dashboard()
    elif selected_page == "Product Management":
        show_product_management()
    elif selected_page == "Order Management":
        show_admin_order_management()
    elif selected_page == "Reports":
        show_reports()

def show_staff_navigation():
    st.sidebar.header("Staff Panel")
    
    pages = {
        "Dashboard": "staff_dashboard",
        "Order Fulfillment": "order_fulfillment",
        "Inventory Check": "inventory_check"
    }
    
    selected_page = st.sidebar.radio("Navigation", list(pages.keys()))
    
    if selected_page == "Dashboard":
        show_staff_dashboard()
    elif selected_page == "Order Fulfillment":
        show_order_fulfillment()
    elif selected_page == "Inventory Check":
        show_inventory_check()

def show_customer_navigation():
    st.sidebar.header("Customer Panel")
    
    pages = {
        "Shop": "shop",
        "My Orders": "my_orders",
        "Shopping Cart": "cart"
    }
    
    selected_page = st.sidebar.radio("Navigation", list(pages.keys()))
    
    if selected_page == "Shop":
        show_shop()
    elif selected_page == "My Orders":
        show_my_orders()
    elif selected_page == "Shopping Cart":
        show_cart()

# Admin Dashboard Functions
def show_admin_dashboard():
    from pages.admin_dashboard import show_admin_dashboard_page
    show_admin_dashboard_page(db)

def show_product_management():
    from pages.product_management import show_product_management_page
    show_product_management_page(db)

def show_admin_order_management():
    from pages.order_management import show_admin_order_management_page
    show_admin_order_management_page(db)

def show_reports():
    st.title("📊 Reports & Analytics")
    
    # Order Statistics
    orders = db.get_all_orders()
    products = db.get_all_products()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Orders", len(orders))
    with col2:
        total_revenue = sum(order.total_amount for order in orders if order.status.value == 'delivered')
        st.metric("Total Revenue", f"${total_revenue:.2f}")
    with col3:
        pending_orders = [o for o in orders if o.status.value in ['placed', 'paid']]
        st.metric("Pending Orders", len(pending_orders))
    with col4:
        low_stock = [p for p in products if p.stock_quantity < 10]
        st.metric("Low Stock Items", len(low_stock))
    
    # Revenue Chart
    if orders:
        import plotly.express as px
        
        df_orders = pd.DataFrame(orders)
        df_orders['created_at'] = pd.to_datetime(df_orders['created_at'])
        df_orders = df_orders[df_orders['status'] == 'delivered']
        
        if not df_orders.empty:
            daily_revenue = df_orders.groupby(df_orders['created_at'].dt.date)['total_amount'].sum().reset_index()
            daily_revenue.columns = ['Date', 'Revenue']
            
            fig = px.line(daily_revenue, x='Date', y='Revenue', title='Daily Revenue')
            st.plotly_chart(fig, use_container_width=True)

# Staff Dashboard Functions
def show_staff_dashboard():
    from pages.staff_dashboard import show_staff_dashboard_page
    show_staff_dashboard_page(db)

def show_order_fulfillment():
    st.title("📋 Order Fulfillment")
    
    orders = [o for o in db.get_all_orders() if o.status.value in ['placed', 'paid']]
    
    if not orders:
        st.info("No pending orders to fulfill.")
        return
    
    for order in orders:
        with st.expander(f"Order #{order.id} - {order.username} - ${order.total_amount:.2f}"):
            st.write(f"**Status:** {order.status.value.title()}")
            st.write(f"**Created:** {order.created_at}")
            
            # Get order items
            items = db.get_order_items(order.id)
            if items:
                st.write("**Items:**")
                for item in items:
                    st.write(f"- {item.product_name} x{item.quantity} @ ${item.unit_price:.2f}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if order.status.value == 'placed' and st.button("Mark as Paid", key=f"pay_{order.id}"):
                    from models import OrderStatus
                    if db.update_order_status(order.id, OrderStatus.PAID):
                        st.success("Order marked as paid!")
                        st.rerun()
            
            with col2:
                if order.status.value == 'paid' and st.button("Mark as Delivered", key=f"deliver_{order.id}"):
                    from models import OrderStatus
                    if db.update_order_status(order.id, OrderStatus.DELIVERED):
                        st.success("Order marked as delivered!")
                        st.rerun()

def show_inventory_check():
    st.title("📦 Inventory Check")
    
    products = db.get_all_products()
    
    if products:
        df = pd.DataFrame(products)
        
        # Low stock alert
        low_stock = df[df['stock_quantity'] < 10]
        if not low_stock.empty:
            st.warning("⚠️ Low Stock Alert!")
            st.dataframe(low_stock[['name', 'stock_quantity', 'price']], use_container_width=True)
        
        st.subheader("All Products")
        st.dataframe(df[['name', 'description', 'stock_quantity', 'price']], use_container_width=True)

# Customer Functions
def show_shop():
    from pages.customer_dashboard import show_shop_page
    show_shop_page(db, st.session_state.username)

def show_my_orders():
    from pages.customer_dashboard import show_my_orders_page
    show_my_orders_page(db, st.session_state.username)

def show_cart():
    from pages.customer_dashboard import show_cart_page
    show_cart_page(db, st.session_state.username)

if __name__ == "__main__":
    main()
