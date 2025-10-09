import streamlit as st
import pandas as pd

def show_shop_page(db, username):
    st.title("🛍️ Shop")
    
    # Search and filters
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_term = st.text_input("🔍 Search products", placeholder="Search by name or description...")
    
    with col2:
        categories = list(set(p['category'] for p in db.get_all_products() if p['category']))
        selected_category = st.selectbox("Category", ["All"] + categories)
    
    with col3:
        sort_by = st.selectbox("Sort by", ["Name", "Price (Low to High)", "Price (High to Low)", "Stock"])
    
    # Get products
    products = db.get_all_products()
    
    # Apply filters
    if search_term:
        products = [p for p in products if 
                   search_term.lower() in p['name'].lower() or 
                   search_term.lower() in (p['description'] or '').lower()]
    
    if selected_category != "All":
        products = [p for p in products if p['category'] == selected_category]
    
    # Apply sorting
    if sort_by == "Name":
        products.sort(key=lambda x: x['name'])
    elif sort_by == "Price (Low to High)":
        products.sort(key=lambda x: x['price'])
    elif sort_by == "Price (High to Low)":
        products.sort(key=lambda x: x['price'], reverse=True)
    elif sort_by == "Stock":
        products.sort(key=lambda x: x['stock_quantity'], reverse=True)
    
    # Display products
    if products:
        # Products grid
        cols = st.columns(3)
        for idx, product in enumerate(products):
            with cols[idx % 3]:
                with st.container():
                    st.markdown(f"### {product['name']}")
                    st.write(f"**Price:** ${product['price']:.2f}")
                    st.write(f"**Stock:** {product['stock_quantity']} available")
                    st.write(f"**Category:** {product['category'] or 'General'}")
                    
                    if product['description']:
                        st.write(f"*{product['description']}*")
                    
                    # Add to cart functionality
                    quantity = st.number_input(
                        "Quantity", 
                        min_value=1, 
                        max_value=product['stock_quantity'] if product['stock_quantity'] > 0 else 1,
                        value=1,
                        key=f"qty_{product['id']}"
                    )
                    
                    if product['stock_quantity'] > 0:
                        if st.button(f"Add to Cart", key=f"add_{product['id']}", type="primary", use_container_width=True):
                            if db.add_to_cart(username, product['id'], quantity):
                                st.success(f"Added {quantity} x {product['name']} to cart!")
                                st.rerun()
                            else:
                                st.error("Failed to add to cart")
                    else:
                        st.error("Out of Stock")
                    
                    st.divider()
    else:
        st.info("No products found matching your criteria.")

def show_my_orders_page(db, username):
    st.title("📋 My Orders")
    
    orders = db.get_user_orders(username)
    
    if orders:
        # Order summary
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_orders = len(orders)
            st.metric("Total Orders", total_orders)
        
        with col2:
            delivered_orders = [o for o in orders if o['status'] == 'delivered']
            st.metric("Delivered Orders", len(delivered_orders))
        
        with col3:
            total_spent = sum(o['total_amount'] for o in delivered_orders)
            st.metric("Total Spent", f"${total_spent:.2f}")
        
        st.divider()
        
        # Orders list
        for order in orders:
            status_color = {
                'placed': '🟡',
                'paid': '🟠', 
                'delivered': '🟢',
                'cancelled': '🔴'
            }.get(order['status'], '⚪')
            
            with st.expander(f"{status_color} Order #{order['id']} - ${order['total_amount']:.2f} - {order['status'].title()}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Order Date:** {order['created_at']}")
                    st.write(f"**Status:** {order['status'].title()}")
                    st.write(f"**Total Amount:** ${order['total_amount']:.2f}")
                
                with col2:
                    st.write(f"**Last Updated:** {order['updated_at']}")
                    
                    # Action buttons
                    if order['status'] == 'placed':
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            if st.button(f"Make Payment", key=f"pay_{order['id']}", type="primary"):
                                if db.update_order_status(order['id'], 'paid'):
                                    st.success("✅ Payment successful!")
                                    st.rerun()
                        
                        with col_btn2:
                            if st.button(f"Cancel Order", key=f"cancel_{order['id']}"):
                                if db.cancel_order(order['id']):
                                    st.success("Order cancelled and inventory restored!")
                                    st.rerun()
                                else:
                                    st.error("Failed to cancel order")
                
                # Show order items
                items = db.get_order_items(order['id'])
                if items:
                    st.write("**Items Ordered:**")
                    for item in items:
                        st.write(f"• {item['product_name']} x{item['quantity']} @ ${item['unit_price']:.2f} = ${item['quantity'] * item['unit_price']:.2f}")
    else:
        st.info("You haven't placed any orders yet.")
        if st.button("Start Shopping", type="primary"):
            st.session_state.page = 'shop'
            st.rerun()

def show_cart_page(db, username):
    st.title("🛒 Shopping Cart")
    
    cart_items = db.get_cart_items(username)
    
    if cart_items:
        # Cart summary
        total_amount = sum(item['quantity'] * item['price'] for item in cart_items)
        total_items = sum(item['quantity'] for item in cart_items)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Items in Cart", total_items)
        with col2:
            st.metric("Total Amount", f"${total_amount:.2f}")
        
        st.divider()
        
        # Cart items
        for item in cart_items:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    st.write(f"**{item['name']}**")
                    st.write(f"${item['price']:.2f} each")
                    st.write(f"Stock: {item['stock_quantity']} available")
                
                with col2:
                    st.write("**Quantity**")
                    st.write(f"{item['quantity']}")
                
                with col3:
                    st.write("**Subtotal**")
                    subtotal = item['quantity'] * item['price']
                    st.write(f"${subtotal:.2f}")
                
                with col4:
                    st.write("**Action**")
                    if st.button("Remove", key=f"remove_{item['product_id']}", type="secondary"):
                        if db.remove_from_cart(username, item['product_id']):
                            st.success("Item removed from cart")
                            st.rerun()
                
                st.divider()
        
        # Checkout section
        st.subheader("💳 Checkout")
        
        # Check stock availability
        stock_issues = []
        for item in cart_items:
            if item['quantity'] > item['stock_quantity']:
                stock_issues.append(f"{item['name']} - Want {item['quantity']}, Only {item['stock_quantity']} available")
        
        if stock_issues:
            st.error("⚠️ Stock Issues:")
            for issue in stock_issues:
                st.write(f"• {issue}")
            st.write("Please update your cart quantities before checkout.")
        else:
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Place Order", type="primary", use_container_width=True):
                    # Reserve inventory and create order
                    can_reserve = True
                    for item in cart_items:
                        if not db.reserve_inventory(item['product_id'], username, item['quantity']):
                            can_reserve = False
                            break
                    
                    if can_reserve:
                        order_id = db.create_order(username, cart_items)
                        if order_id:
                            st.success(f"✅ Order #{order_id} placed successfully!")
                            st.balloons()
                            st.rerun()
                        else:
                            # Release reservations if order creation failed
                            for item in cart_items:
                                db.release_reservation(item['product_id'], username, item['quantity'])
                            st.error("Failed to create order. Please try again.")
                    else:
                        st.error("Unable to reserve inventory. Some items may be out of stock.")
            
            with col2:
                if st.button("Clear Cart", type="secondary", use_container_width=True):
                    if db.clear_cart(username):
                        st.success("Cart cleared")
                        st.rerun()
    else:
        st.info("Your cart is empty.")
        if st.button("Start Shopping", type="primary"):
            st.session_state.page = 'shop'
            st.rerun()
