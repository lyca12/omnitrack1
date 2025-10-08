import streamlit as st
import pandas as pd

def show_staff_dashboard_page(db):
    st.title("👥 Staff Dashboard")
    
    # Get data
    orders = db.get_all_orders()
    products = db.get_all_products()
    
    # Quick Stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        pending_orders = [o for o in orders if o['status'] in ['placed', 'paid']]
        st.metric("Orders to Process", len(pending_orders))
    
    with col2:
        placed_orders = [o for o in orders if o['status'] == 'placed']
        st.metric("Awaiting Payment", len(placed_orders))
    
    with col3:
        paid_orders = [o for o in orders if o['status'] == 'paid']
        st.metric("Ready to Ship", len(paid_orders))
    
    with col4:
        low_stock = [p for p in products if p['stock_quantity'] < 10]
        st.metric("Low Stock Items", len(low_stock))
    
    st.divider()
    
    # Priority Actions
    st.subheader("🎯 Priority Actions")
    
    # Orders needing attention
    if placed_orders:
        st.warning(f"⚠️ {len(placed_orders)} orders are awaiting payment confirmation")
    
    if paid_orders:
        st.info(f"📦 {len(paid_orders)} orders are ready for delivery")
    
    if low_stock:
        st.error(f"📉 {len(low_stock)} products are running low on stock")
    
    if not placed_orders and not paid_orders and not low_stock:
        st.success("✅ All caught up! No immediate actions needed.")
    
    # Recent Activity
    st.subheader("📋 Recent Order Activity")
    
    if orders:
        recent_orders = orders[:15]  # Show last 15 orders
        
        for order in recent_orders:
            status_color = {
                'placed': '🟡',
                'paid': '🟠', 
                'delivered': '🟢',
                'cancelled': '🔴'
            }.get(order['status'], '⚪')
            
            with st.expander(f"{status_color} Order #{order['id']} - {order['username']} - ${order['total_amount']:.2f}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Customer:** {order['username']}")
                    st.write(f"**Status:** {order['status'].title()}")
                    st.write(f"**Total:** ${order['total_amount']:.2f}")
                
                with col2:
                    st.write(f"**Created:** {order['created_at']}")
                    st.write(f"**Updated:** {order['updated_at']}")
                
                # Show items
                items = db.get_order_items(order['id'])
                if items:
                    st.write("**Items:**")
                    for item in items:
                        st.write(f"• {item['product_name']} x{item['quantity']} @ ${item['unit_price']:.2f}")
                
                # Quick action buttons for staff
                if order['status'] == 'placed':
                    if st.button(f"Mark as Paid", key=f"staff_pay_{order['id']}", type="primary"):
                        if db.update_order_status(order['id'], 'paid'):
                            st.success("✅ Order marked as paid!")
                            st.rerun()
                
                elif order['status'] == 'paid':
                    if st.button(f"Mark as Delivered", key=f"staff_deliver_{order['id']}", type="primary"):
                        if db.update_order_status(order['id'], 'delivered'):
                            st.success("✅ Order marked as delivered!")
                            st.rerun()
    else:
        st.info("No orders to display")
    
    # Inventory Overview
    st.subheader("📦 Inventory Overview")
    
    if products:
        df_products = pd.DataFrame(products)
        
        # Show low stock items first
        if low_stock:
            st.write("**🔴 Low Stock Items:**")
            df_low = pd.DataFrame(low_stock)
            st.dataframe(
                df_low[['name', 'stock_quantity', 'price', 'category']],
                use_container_width=True
            )
        
        # All products summary
        st.write("**All Products:**")
        st.dataframe(
            df_products[['name', 'stock_quantity', 'price', 'category']],
            use_container_width=True
        )
    else:
        st.info("No products found")
