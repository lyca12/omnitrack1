import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

def format_currency(amount):
    """Format amount as currency"""
    return f"${amount:.2f}"

def format_datetime(dt_string):
    """Format datetime string for display"""
    try:
        dt = datetime.fromisoformat(dt_string)
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return dt_string

def get_status_color(status):
    """Get color for order status"""
    colors = {
        'placed': '🟡',
        'paid': '🟠',
        'delivered': '🟢',
        'cancelled': '🔴'
    }
    return colors.get(status, '⚪')

def check_low_stock(products, threshold=10):
    """Check for products with low stock"""
    return [p for p in products if p['stock_quantity'] < threshold]

def calculate_order_metrics(orders):
    """Calculate order metrics"""
    if not orders:
        return {
            'total_orders': 0,
            'total_revenue': 0,
            'avg_order_value': 0,
            'completion_rate': 0
        }
    
    delivered_orders = [o for o in orders if o['status'] == 'delivered']
    total_revenue = sum(o['total_amount'] for o in delivered_orders)
    avg_order_value = total_revenue / len(delivered_orders) if delivered_orders else 0
    completion_rate = len(delivered_orders) / len(orders) * 100 if orders else 0
    
    return {
        'total_orders': len(orders),
        'total_revenue': total_revenue,
        'avg_order_value': avg_order_value,
        'completion_rate': completion_rate
    }

def create_summary_metrics(col1, col2, col3, col4, metrics):
    """Create summary metrics display"""
    with col1:
        st.metric("Total Orders", metrics['total_orders'])
    
    with col2:
        st.metric("Total Revenue", format_currency(metrics['total_revenue']))
    
    with col3:
        st.metric("Avg Order Value", format_currency(metrics['avg_order_value']))
    
    with col4:
        st.metric("Completion Rate", f"{metrics['completion_rate']:.1f}%")

def show_low_stock_alert(products, threshold=10):
    """Show low stock alert"""
    low_stock_items = check_low_stock(products, threshold)
    
    if low_stock_items:
        st.warning(f"⚠️ {len(low_stock_items)} items are low on stock (< {threshold} units)")
        
        with st.expander("View Low Stock Items"):
            for item in low_stock_items:
                st.write(f"• **{item['name']}** - Only {item['stock_quantity']} left")
        
        return True
    return False

def validate_product_data(name, price, stock, category=None):
    """Validate product data"""
    errors = []
    
    if not name or len(name.strip()) == 0:
        errors.append("Product name is required")
    
    if price <= 0:
        errors.append("Price must be greater than 0")
    
    if stock < 0:
        errors.append("Stock quantity cannot be negative")
    
    return errors

def export_orders_to_csv(orders):
    """Export orders to CSV format"""
    if not orders:
        return None
    
    df = pd.DataFrame(orders)
    return df.to_csv(index=False)

def get_order_status_counts(orders):
    """Get count of orders by status"""
    status_counts = {'placed': 0, 'paid': 0, 'delivered': 0, 'cancelled': 0}
    
    for order in orders:
        status = order['status']
        if status in status_counts:
            status_counts[status] += 1
    
    return status_counts

def filter_orders_by_date_range(orders, start_date, end_date):
    """Filter orders by date range"""
    filtered_orders = []
    
    for order in orders:
        try:
            order_date = datetime.fromisoformat(order['created_at']).date()
            if start_date <= order_date <= end_date:
                filtered_orders.append(order)
        except:
            continue
    
    return filtered_orders

def calculate_inventory_value(products):
    """Calculate total inventory value"""
    return sum(p['stock_quantity'] * p['price'] for p in products)

def get_top_selling_products(orders, limit=10):
    """Get top selling products from order data"""
    product_sales = {}
    
    # This would require joining with order_items table
    # For now, return empty list as this requires more complex DB queries
    return []

def show_success_message(message):
    """Show success message with icon"""
    st.success(f"✅ {message}")

def show_error_message(message):
    """Show error message with icon"""
    st.error(f"❌ {message}")

def show_info_message(message):
    """Show info message with icon"""
    st.info(f"ℹ️ {message}")

def show_warning_message(message):
    """Show warning message with icon"""
    st.warning(f"⚠️ {message}")
