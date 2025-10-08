import streamlit as st
import pandas as pd

def show_product_management_page(db):
    st.title("📦 Product Management")
    
    tab1, tab2, tab3 = st.tabs(["View Products", "Add Product", "Update Stock"])
    
    with tab1:
        show_products_list(db)
    
    with tab2:
        show_add_product(db)
    
    with tab3:
        show_update_stock(db)

def show_products_list(db):
    st.subheader("All Products")
    
    products = db.get_all_products()
    
    if products:
        df = pd.DataFrame(products)
        
        # Display options
        col1, col2 = st.columns(2)
        with col1:
            show_low_stock = st.checkbox("Show only low stock items (< 10)")
        with col2:
            category_filter = st.selectbox("Filter by category", ["All"] + list(set(p['category'] for p in products if p['category'])))
        
        # Apply filters
        filtered_products = products.copy()
        
        if show_low_stock:
            filtered_products = [p for p in filtered_products if p['stock_quantity'] < 10]
        
        if category_filter != "All":
            filtered_products = [p for p in filtered_products if p['category'] == category_filter]
        
        if filtered_products:
            # Create display dataframe
            df_display = pd.DataFrame(filtered_products)
            
            # Format columns for display
            df_display = df_display[['id', 'name', 'category', 'price', 'stock_quantity', 'description']]
            df_display.columns = ['ID', 'Name', 'Category', 'Price ($)', 'Stock', 'Description']
            
            # Color code low stock items
            def highlight_low_stock(row):
                if row['Stock'] < 10:
                    return ['background-color: #ffebee'] * len(row)
                return [''] * len(row)
            
            st.dataframe(
                df_display.style.apply(highlight_low_stock, axis=1),
                use_container_width=True
            )
            
            # Show low stock warning
            low_stock_items = [p for p in filtered_products if p['stock_quantity'] < 10]
            if low_stock_items and not show_low_stock:
                st.warning(f"⚠️ {len(low_stock_items)} items are low on stock!")
        else:
            st.info("No products match the current filters.")
    else:
        st.info("No products found. Add some products to get started.")

def show_add_product(db):
    st.subheader("Add New Product")
    
    with st.form("add_product_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Product Name*", placeholder="e.g., Basketball")
            price = st.number_input("Price ($)*", min_value=0.01, format="%.2f")
            stock = st.number_input("Initial Stock*", min_value=0, value=0)
        
        with col2:
            category = st.text_input("Category", placeholder="e.g., Sports")
            description = st.text_area("Description", placeholder="Product description...")
        
        submitted = st.form_submit_button("Add Product", type="primary")
        
        if submitted:
            if not name or price <= 0:
                st.error("Please fill in all required fields with valid values.")
            else:
                try:
                    product_id = db.add_product(name, description, price, stock, category)
                    st.success(f"✅ Product '{name}' added successfully with ID #{product_id}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding product: {str(e)}")

def show_update_stock(db):
    st.subheader("Update Product Stock")
    
    products = db.get_all_products()
    
    if products:
        # Select product
        product_options = {f"{p['name']} (ID: {p['id']})": p for p in products}
        selected_product_key = st.selectbox("Select Product", list(product_options.keys()))
        
        if selected_product_key:
            selected_product = product_options[selected_product_key]
            
            # Current stock info
            st.info(f"Current stock: **{selected_product['stock_quantity']}** units")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Add Stock (Restock)**")
                with st.form("add_stock_form"):
                    add_quantity = st.number_input("Quantity to Add", min_value=1, value=1)
                    add_notes = st.text_input("Notes (optional)", placeholder="e.g., Weekly restock")
                    
                    if st.form_submit_button("Add Stock", type="primary"):
                        new_stock = selected_product['stock_quantity'] + add_quantity
                        if db.update_product_stock(selected_product['id'], new_stock, 'restock', add_notes):
                            st.success(f"✅ Added {add_quantity} units to {selected_product['name']}")
                            st.rerun()
                        else:
                            st.error("Failed to update stock")
            
            with col2:
                st.write("**Set Stock (Direct Update)**")
                with st.form("set_stock_form"):
                    new_stock = st.number_input(
                        "New Stock Quantity", 
                        min_value=0, 
                        value=selected_product['stock_quantity']
                    )
                    set_notes = st.text_input("Notes (optional)", placeholder="e.g., Inventory correction")
                    
                    if st.form_submit_button("Update Stock", type="secondary"):
                        if db.update_product_stock(selected_product['id'], new_stock, 'manual_update', set_notes):
                            st.success(f"✅ Stock for {selected_product['name']} updated to {new_stock}")
                            st.rerun()
                        else:
                            st.error("Failed to update stock")
            
            # Show recent transactions for this product
            st.subheader("Recent Stock Movements")
            transactions = db.get_inventory_transactions(selected_product['id'])
            
            if transactions:
                recent_transactions = transactions[:10]  # Show last 10
                df_transactions = pd.DataFrame(recent_transactions)
                
                df_display = df_transactions[['transaction_type', 'quantity_change', 'notes', 'created_at']].copy()
                df_display.columns = ['Type', 'Change', 'Notes', 'Date']
                
                # Color code transaction types
                def highlight_transactions(row):
                    if row['Change'] > 0:
                        return ['background-color: #e8f5e8'] * len(row)  # Green for additions
                    elif row['Change'] < 0:
                        return ['background-color: #ffeaa7'] * len(row)  # Yellow for reductions
                    return [''] * len(row)
                
                st.dataframe(
                    df_display.style.apply(highlight_transactions, axis=1),
                    use_container_width=True
                )
            else:
                st.info("No stock movements recorded for this product.")
    else:
        st.info("No products available. Please add products first.")
