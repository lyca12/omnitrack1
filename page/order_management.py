import streamlit as st
import pandas as pd

def show_admin_order_management_page(db):
    st.title("📋 Order Management")
    
    tab1, tab2, tab3 = st.tabs(["All Orders", "Order Analytics", "Order Actions"])
    
    with tab1:
        show_all_orders(db)
    
    with tab2:
        show_order_analytics(db)
    
    with tab3:
        show_order_actions(db)

def show_all_orders(db):
    st.subheader("All Orders")
    
    orders = db.get_all_orders()
    
    if orders:
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All", "placed", "paid", "delivered", "cancelled"]
            )
        
        with col2:
            # Get unique usernames
            usernames = list(set(order['username'] for order in orders))
            user_filter = st.selectbox("Filter by Customer", ["All"] + usernames)
        
        with col3:
            sort_by = st.selectbox("Sort by", ["Recent First", "Oldest First", "Amount (High to Low)", "Amount (Low to High)"])
        
        # Apply filters
        filtered_orders = orders.copy()
        
        if status_filter != "All":
            filtered_orders = [o for o in filtered_orders if o['status'] == status_filter]
        
        if user_filter != "All":
            filtered_orders = [o for o in filtered_orders if o['username'] == user_filter]
        
        # Apply sorting
        if sort_by == "Recent First":
            filtered_orders.sort(key=lambda x: x['created_at'], reverse=True)
        elif sort_by == "Oldest First":
            filtered_orders.sort(key=lambda x: x['created_at'])
        elif sort_by == "Amount (High to Low)":
            filtered_orders.sort(key=lambda x: x['total_amount'], reverse=True)
        elif sort_by == "Amount (Low to High)":
            filtered_orders.sort(key=lambda x: x['total_amount'])
        
        # Display orders
        if filtered_orders:
            for order in filtered_orders:
                status_color = {
                    'placed': '🟡',
                    'paid': '🟠', 
                    'delivered': '🟢',
                    'cancelled': '🔴'
                }.get(order['status'], '⚪')
                
                with st.expander(
                    f"{status_color} Order #{order['id']} - {order['username']} - ${order['total_amount']:.2f} - {order['status'].title()}"
                ):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Customer:** {order['username']}")
                        st.write(f"**Status:** {order['status'].title()}")
                        st.write(f"**Total Amount:** ${order['total_amount']:.2f}")
                    
                    with col2:
                        st.write(f"**Order Date:** {order['created_at']}")
                        st.write(f"**Last Updated:** {order['updated_at']}")
                    
                    # Order items
                    items = db.get_order_items(order['id'])
                    if items:
                        st.write("**Order Items:**")
                        items_df = pd.DataFrame(items)
                        items_df['subtotal'] = items_df['quantity'] * items_df['unit_price']
                        
                        display_df = items_df[['product_name', 'quantity', 'unit_price', 'subtotal']]
                        display_df.columns = ['Product', 'Qty', 'Unit Price ($)', 'Subtotal ($)']
                        st.dataframe(display_df, use_container_width=True)
                    
                    # Admin actions
                    if order['status'] != 'cancelled' and order['status'] != 'delivered':
                        st.write("**Admin Actions:**")
                        action_col1, action_col2, action_col3 = st.columns(3)
                        
                        with action_col1:
                            if order['status'] == 'placed' and st.button(f"Mark as Paid", key=f"admin_pay_{order['id']}"):
                                if db.update_order_status(order['id'], 'paid'):
                                    st.success("Order marked as paid!")
                                    st.rerun()
                        
                        with action_col2:
                            if order['status'] == 'paid' and st.button(f"Mark as Delivered", key=f"admin_deliver_{order['id']}"):
                                if db.update_order_status(order['id'], 'delivered'):
                                    st.success("Order marked as delivered!")
                                    st.rerun()
                        
                        with action_col3:
                            if order['status'] in ['placed', 'paid'] and st.button(f"Cancel Order", key=f"admin_cancel_{order['id']}"):
                                if db.cancel_order(order['id']):
                                    st.success("Order cancelled and inventory restored!")
                                    st.rerun()
                                else:
                                    st.error("Failed to cancel order")
        else:
            st.info("No orders match the current filters.")
    else:
        st.info("No orders found.")

def show_order_analytics(db):
    st.subheader("Order Analytics")
    
    orders = db.get_all_orders()
    
    if orders:
        import plotly.express as px
        import plotly.graph_objects as go
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Orders", len(orders))
        
        with col2:
            avg_order_value = sum(o['total_amount'] for o in orders) / len(orders)
            st.metric("Avg Order Value", f"${avg_order_value:.2f}")
        
        with col3:
            delivered_orders = [o for o in orders if o['status'] == 'delivered']
            completion_rate = len(delivered_orders) / len(orders) * 100
            st.metric("Completion Rate", f"{completion_rate:.1f}%")
        
        with col4:
            total_revenue = sum(o['total_amount'] for o in delivered_orders)
            st.metric("Total Revenue", f"${total_revenue:.2f}")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Status distribution
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
        
        with col2:
            # Orders by customer
            customer_orders = {}
            for order in orders:
                customer = order['username']
                if customer not in customer_orders:
                    customer_orders[customer] = {'count': 0, 'total': 0}
                customer_orders[customer]['count'] += 1
                customer_orders[customer]['total'] += order['total_amount']
            
            # Top customers by order count
            top_customers = sorted(customer_orders.items(), key=lambda x: x[1]['count'], reverse=True)[:10]
            
            if top_customers:
                customers = [c[0] for c in top_customers]
                counts = [c[1]['count'] for c in top_customers]
                
                fig_customers = px.bar(
                    x=counts,
                    y=customers,
                    orientation='h',
                    title="Top Customers by Order Count"
                )
                fig_customers.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_customers, use_container_width=True)
        
        # Order timeline
        if delivered_orders:
            df_orders = pd.DataFrame(delivered_orders)
            df_orders['created_at'] = pd.to_datetime(df_orders['created_at'])
            
            # Daily orders
            daily_orders = df_orders.groupby(df_orders['created_at'].dt.date).agg({
                'id': 'count',
                'total_amount': 'sum'
            }).reset_index()
            daily_orders.columns = ['Date', 'Order Count', 'Revenue']
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_daily_orders = px.line(daily_orders, x='Date', y='Order Count', title='Daily Order Count')
                st.plotly_chart(fig_daily_orders, use_container_width=True)
            
            with col2:
                fig_daily_revenue = px.line(daily_orders, x='Date', y='Revenue', title='Daily Revenue')
                st.plotly_chart(fig_daily_revenue, use_container_width=True)
    else:
        st.info("No order data available for analytics.")

def show_order_actions(db):
    st.subheader("Bulk Order Actions")
    
    orders = db.get_all_orders()
    pending_orders = [o for o in orders if o['status'] in ['placed', 'paid']]
    
    if pending_orders:
        st.write("**Bulk Actions for Pending Orders:**")
        
        # Mark multiple orders as paid
        placed_orders = [o for o in pending_orders if o['status'] == 'placed']
        if placed_orders:
            st.write("**Mark as Paid:**")
            for order in placed_orders:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"Order #{order['id']} - {order['username']} - ${order['total_amount']:.2f}")
                with col2:
                    if st.button("Mark Paid", key=f"bulk_pay_{order['id']}", type="secondary"):
                        if db.update_order_status(order['id'], 'paid'):
                            st.success(f"Order #{order['id']} marked as paid!")
                            st.rerun()
        
        st.divider()
        
        # Mark multiple orders as delivered
        paid_orders = [o for o in pending_orders if o['status'] == 'paid']
        if paid_orders:
            st.write("**Mark as Delivered:**")
            for order in paid_orders:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"Order #{order['id']} - {order['username']} - ${order['total_amount']:.2f}")
                with col2:
                    if st.button("Mark Delivered", key=f"bulk_deliver_{order['id']}", type="primary"):
                        if db.update_order_status(order['id'], 'delivered'):
                            st.success(f"Order #{order['id']} marked as delivered!")
                            st.rerun()
    else:
        st.success("✅ No pending orders! All orders are either delivered or cancelled.")
