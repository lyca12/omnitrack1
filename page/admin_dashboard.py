import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

def show_admin_dashboard_page(db):
    st.title("📊 Admin Dashboard")
    
    # Get data
    products = db.get_all_products()
    orders = db.get_all_orders()
    transactions = db.get_inventory_transactions()
    
    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Products", len(products))
    
    with col2:
        total_orders = len(orders)
        st.metric("Total Orders", total_orders)
    
    with col3:
        delivered_orders = [o for o in orders if o['status'] == 'delivered']
        total_revenue = sum(order['total_amount'] for order in delivered_orders)
        st.metric("Total Revenue", f"${total_revenue:.2f}")
    
    with col4:
        pending_orders = [o for o in orders if o['status'] in ['placed', 'paid']]
        st.metric("Pending Orders", len(pending_orders))
    
    st.divider()
    
    # Charts Row
    col1, col2 = st.columns(2)
    
    with col1:
        # Order Status Distribution
        if orders:
            status_counts = {}
            for order in orders:
                status = order['status']
                status_counts[status] = status_counts.get(status, 0) + 1
            
            fig_status = px.pie(
                values=list(status_counts.values()),
                names=list(status_counts.keys()),
                title="Order Status Distribution"
            )
            st.plotly_chart(fig_status, use_container_width=True)
        else:
            st.info("No orders data available")
    
    with col2:
        # Revenue Trend
        if delivered_orders:
            df_revenue = pd.DataFrame(delivered_orders)
            df_revenue['created_at'] = pd.to_datetime(df_revenue['created_at'])
            df_revenue = df_revenue.set_index('created_at')
            daily_revenue = df_revenue.resample('D')['total_amount'].sum().reset_index()
            
            fig_revenue = px.line(
                daily_revenue,
                x='created_at',
                y='total_amount',
                title="Daily Revenue Trend"
            )
            st.plotly_chart(fig_revenue, use_container_width=True)
        else:
            st.info("No revenue data available")
    
    # Low Stock Alerts
    st.subheader("⚠️ Low Stock Alerts")
    low_stock_products = [p for p in products if p['stock_quantity'] < 10]
    
    if low_stock_products:
        df_low_stock = pd.DataFrame(low_stock_products)
        st.dataframe(
            df_low_stock[['name', 'stock_quantity', 'price', 'category']],
            use_container_width=True
        )
    else:
        st.success("No low stock items!")
    
    # Recent Orders
    st.subheader("📋 Recent Orders")
    if orders:
        recent_orders = orders[:10]  # Last 10 orders
        
        for order in recent_orders:
            status_color = {
                'placed': '🟡',
                'paid': '🟠', 
                'delivered': '🟢',
                'cancelled': '🔴'
            }.get(order['status'], '⚪')
            
            with st.expander(f"{status_color} Order #{order['id']} - {order['username']} - ${order['total_amount']:.2f}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Status:** {order['status'].title()}")
                
                with col2:
                    st.write(f"**Created:** {order['created_at']}")
                
                with col3:
                    st.write(f"**Total:** ${order['total_amount']:.2f}")
                
                # Order items
                items = db.get_order_items(order['id'])
                if items:
                    st.write("**Items:**")
                    for item in items:
                        st.write(f"• {item['product_name']} x{item['quantity']} @ ${item['unit_price']:.2f}")
    else:
        st.info("No orders found")
    
    # Inventory Activity
    st.subheader("📦 Recent Inventory Activity")
    if transactions:
        recent_transactions = transactions[:20]  # Last 20 transactions
        df_transactions = pd.DataFrame(recent_transactions)
        
        # Format the dataframe
        df_display = df_transactions[[
            'product_name', 'transaction_type', 'quantity_change', 
            'notes', 'created_at'
        ]].copy()
        
        df_display.columns = ['Product', 'Type', 'Quantity Change', 'Notes', 'Date']
        
        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("No inventory transactions found")
