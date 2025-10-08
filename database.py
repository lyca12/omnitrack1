import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
import threading
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        self.lock = threading.Lock()
        self.init_database()
        self.create_demo_data()
    
    def get_connection(self):
        conn = psycopg2.connect(self.database_url)
        return conn
    
    def init_database(self):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(50) NOT NULL DEFAULT 'customer',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Products table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    price DECIMAL(10, 2) NOT NULL,
                    stock_quantity INTEGER NOT NULL DEFAULT 0,
                    category VARCHAR(100),
                    sku VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Orders table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(255) NOT NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'placed',
                    total_amount DECIMAL(10, 2) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Order items table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS order_items (
                    id SERIAL PRIMARY KEY,
                    order_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    product_name VARCHAR(255) NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price DECIMAL(10, 2) NOT NULL,
                    FOREIGN KEY (order_id) REFERENCES orders (id),
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            """)
            
            # Inventory transactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inventory_transactions (
                    id SERIAL PRIMARY KEY,
                    product_id INTEGER NOT NULL,
                    transaction_type VARCHAR(50) NOT NULL,
                    quantity_change INTEGER NOT NULL,
                    reference_id VARCHAR(100),
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            """)
            
            # Shopping cart table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shopping_cart (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(255) NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            """)
            
            # Reserved inventory table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reserved_inventory (
                    id SERIAL PRIMARY KEY,
                    product_id INTEGER NOT NULL,
                    username VARCHAR(255) NOT NULL,
                    quantity INTEGER NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            """)
            
            conn.commit()
            conn.close()
    
    def create_demo_data(self):
        """Create demo data if products table is empty"""
        products = self.get_all_products()
        if not products:
            demo_products = [
                ("Basketball", "Professional basketball", 29.99, 50, "Sports", "SPT-BB-001"),
                ("Soccer Ball", "FIFA approved soccer ball", 24.99, 30, "Sports", "SPT-SB-002"),
                ("Tennis Racket", "Professional tennis racket", 89.99, 15, "Sports", "SPT-TR-003"),
                ("Running Shoes", "Comfortable running shoes", 79.99, 25, "Footwear", "FTW-RS-004"),
                ("Gym Bag", "Large sports gym bag", 34.99, 40, "Accessories", "ACC-GB-005"),
                ("Water Bottle", "Stainless steel water bottle", 19.99, 100, "Accessories", "ACC-WB-006"),
                ("Yoga Mat", "Non-slip yoga mat", 39.99, 20, "Fitness", "FIT-YM-007"),
                ("Dumbbells", "Set of adjustable dumbbells", 149.99, 10, "Fitness", "FIT-DB-008"),
                ("Cricket Bat", "Professional cricket bat", 69.99, 8, "Sports", "SPT-CB-009"),
                ("Hockey Stick", "Ice hockey stick", 59.99, 12, "Sports", "SPT-HS-010")
            ]
            
            for name, desc, price, stock, category, sku in demo_products:
                self.add_product(name, desc, price, stock, category, sku)
    
    # User management
    def create_user(self, username: str, password_hash: str, role: str = 'customer') -> bool:
        try:
            with self.lock:
                conn = self.get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                    (username, password_hash, role)
                )
                conn.commit()
                conn.close()
                return True
        except psycopg2.IntegrityError:
            return False
    
    def get_user(self, username: str) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    # Product management
    def add_product(self, name: str, description: str, price: float, stock: int, category: str = None, sku: str = None) -> int:
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO products (name, description, price, stock_quantity, category, sku) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                (name, description, price, stock, category, sku)
            )
            product_id = cursor.fetchone()[0]
            
            # Log inventory transaction (same connection to ensure transaction integrity)
            cursor.execute(
                "INSERT INTO inventory_transactions (product_id, transaction_type, quantity_change, notes) VALUES (%s, %s, %s, %s)",
                (product_id, 'initial_stock', stock, 'Initial stock')
            )
            
            conn.commit()
            conn.close()
            return product_id
    
    def get_all_products(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM products ORDER BY name")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_product(self, product_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def update_product_stock(self, product_id: int, new_stock: int, transaction_type: str = 'manual_update', notes: str = None) -> bool:
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Get current stock
            cursor.execute("SELECT stock_quantity FROM products WHERE id = %s", (product_id,))
            result = cursor.fetchone()
            if not result:
                conn.close()
                return False
            
            old_stock = result[0]
            quantity_change = new_stock - old_stock
            
            # Update stock
            cursor.execute(
                "UPDATE products SET stock_quantity = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (new_stock, product_id)
            )
            
            # Log transaction (same cursor to ensure atomicity)
            self.log_inventory_transaction(product_id, transaction_type, quantity_change, notes, cursor=cursor)
            
            conn.commit()
            conn.close()
            return True
    
    def reserve_inventory(self, product_id: int, username: str, quantity: int) -> bool:
        """Reserve inventory for a user temporarily"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check available stock
            cursor.execute("SELECT stock_quantity FROM products WHERE id = %s", (product_id,))
            result = cursor.fetchone()
            if not result or result[0] < quantity:
                conn.close()
                return False
            
            # Create reservation (expires in 30 minutes)
            cursor.execute(
                "INSERT INTO reserved_inventory (product_id, username, quantity, expires_at) VALUES (%s, %s, %s, CURRENT_TIMESTAMP + INTERVAL '30 minutes')",
                (product_id, username, quantity)
            )
            
            # Update available stock
            new_stock = result[0] - quantity
            cursor.execute(
                "UPDATE products SET stock_quantity = %s WHERE id = %s",
                (new_stock, product_id)
            )
            
            # Log transaction (same cursor to ensure atomicity)
            self.log_inventory_transaction(product_id, 'reserve', -quantity, f'Reserved for {username}', cursor=cursor)
            
            conn.commit()
            conn.close()
            return True
    
    def release_reservation(self, product_id: int, username: str, quantity: int) -> bool:
        """Release reserved inventory back to available stock"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Remove reservation
            cursor.execute(
                "DELETE FROM reserved_inventory WHERE product_id = %s AND username = %s AND quantity = %s",
                (product_id, username, quantity)
            )
            
            # Update available stock
            cursor.execute("SELECT stock_quantity FROM products WHERE id = %s", (product_id,))
            result = cursor.fetchone()
            if result:
                new_stock = result[0] + quantity
                cursor.execute(
                    "UPDATE products SET stock_quantity = %s WHERE id = %s",
                    (new_stock, product_id)
                )
                
                # Log transaction (same cursor to ensure atomicity)
                self.log_inventory_transaction(product_id, 'release', quantity, f'Released from {username}', cursor=cursor)
            
            conn.commit()
            conn.close()
            return True
    
    def log_inventory_transaction(self, product_id: int, transaction_type: str, quantity_change: int, notes: str = None, reference_id: str = None, cursor=None):
        """Log inventory transaction - if cursor provided, uses it (for transaction safety), otherwise creates new connection"""
        if cursor:
            # Use provided cursor (part of existing transaction)
            cursor.execute(
                "INSERT INTO inventory_transactions (product_id, transaction_type, quantity_change, reference_id, notes) VALUES (%s, %s, %s, %s, %s)",
                (product_id, transaction_type, quantity_change, reference_id, notes)
            )
        else:
            # Standalone transaction
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO inventory_transactions (product_id, transaction_type, quantity_change, reference_id, notes) VALUES (%s, %s, %s, %s, %s)",
                (product_id, transaction_type, quantity_change, reference_id, notes)
            )
            conn.commit()
            conn.close()
    
    # Shopping Cart
    def add_to_cart(self, username: str, product_id: int, quantity: int) -> bool:
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check if item already in cart
            cursor.execute(
                "SELECT quantity FROM shopping_cart WHERE username = %s AND product_id = %s",
                (username, product_id)
            )
            result = cursor.fetchone()
            
            if result:
                # Update quantity
                new_quantity = result[0] + quantity
                cursor.execute(
                    "UPDATE shopping_cart SET quantity = %s WHERE username = %s AND product_id = %s",
                    (new_quantity, username, product_id)
                )
            else:
                # Add new item
                cursor.execute(
                    "INSERT INTO shopping_cart (username, product_id, quantity) VALUES (%s, %s, %s)",
                    (username, product_id, quantity)
                )
            
            conn.commit()
            conn.close()
            return True
    
    def get_cart_items(self, username: str) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT c.*, p.name, p.price, p.stock_quantity
            FROM shopping_cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.username = %s
        """, (username,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def remove_from_cart(self, username: str, product_id: int) -> bool:
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM shopping_cart WHERE username = %s AND product_id = %s",
                (username, product_id)
            )
            conn.commit()
            conn.close()
            return True
    
    def clear_cart(self, username: str) -> bool:
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM shopping_cart WHERE username = %s", (username,))
            conn.commit()
            conn.close()
            return True
    
    # Order management
    def create_order(self, username: str, cart_items: List[Dict]) -> Optional[int]:
        if not cart_items:
            return None
        
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            try:
                # Calculate total
                total_amount = sum(item['quantity'] * float(item['price']) for item in cart_items)
                
                # Create order
                cursor.execute(
                    "INSERT INTO orders (username, total_amount) VALUES (%s, %s) RETURNING id",
                    (username, total_amount)
                )
                order_id = cursor.fetchone()[0]
                
                # Add order items and update inventory
                for item in cart_items:
                    cursor.execute(
                        "INSERT INTO order_items (order_id, product_id, product_name, quantity, unit_price) VALUES (%s, %s, %s, %s, %s)",
                        (order_id, item['product_id'], item['name'], item['quantity'], item['price'])
                    )
                    
                    # Log inventory transaction for sale (same cursor to ensure atomicity)
                    self.log_inventory_transaction(
                        item['product_id'], 
                        'sale', 
                        -item['quantity'], 
                        f'Order #{order_id}',
                        str(order_id),
                        cursor=cursor
                    )
                
                # Clear cart
                cursor.execute("DELETE FROM shopping_cart WHERE username = %s", (username,))
                
                conn.commit()
                conn.close()
                return order_id
                
            except Exception as e:
                conn.rollback()
                conn.close()
                return None
    
    def get_user_orders(self, username: str) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            "SELECT * FROM orders WHERE username = %s ORDER BY created_at DESC",
            (username,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_all_orders(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM orders ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_order_items(self, order_id: int) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            "SELECT * FROM order_items WHERE order_id = %s",
            (order_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def update_order_status(self, order_id: int, status: str) -> bool:
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE orders SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (status, order_id)
            )
            affected = cursor.rowcount > 0
            conn.commit()
            conn.close()
            return affected
    
    def cancel_order(self, order_id: int) -> bool:
        """Cancel an order and restore inventory"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            try:
                # Get order items
                cursor.execute("SELECT * FROM order_items WHERE order_id = %s", (order_id,))
                items = cursor.fetchall()
                
                # Check if order can be cancelled
                cursor.execute("SELECT status FROM orders WHERE id = %s", (order_id,))
                result = cursor.fetchone()
                if not result or result['status'] not in ['placed', 'paid']:
                    conn.close()
                    return False
                
                # Restore inventory
                for item in items:
                    cursor.execute(
                        "UPDATE products SET stock_quantity = stock_quantity + %s WHERE id = %s",
                        (item['quantity'], item['product_id'])
                    )
                    
                    # Log inventory transaction (same cursor to ensure atomicity)
                    self.log_inventory_transaction(
                        item['product_id'],
                        'return',
                        item['quantity'],
                        f'Order #{order_id} cancelled',
                        str(order_id),
                        cursor=cursor
                    )
                
                # Update order status
                cursor.execute(
                    "UPDATE orders SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                    (order_id,)
                )
                
                conn.commit()
                conn.close()
                return True
                
            except Exception as e:
                conn.rollback()
                conn.close()
                return False
    
    # Inventory transactions
    def get_inventory_transactions(self, product_id: int = None) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        if product_id:
            cursor.execute("""
                SELECT t.*, p.name as product_name
                FROM inventory_transactions t
                JOIN products p ON t.product_id = p.id
                WHERE t.product_id = %s
                ORDER BY t.created_at DESC
            """, (product_id,))
        else:
            cursor.execute("""
                SELECT t.*, p.name as product_name
                FROM inventory_transactions t
                JOIN products p ON t.product_id = p.id
                ORDER BY t.created_at DESC
            """)
        
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    # CSV Import/Export methods
    def export_products_to_csv(self) -> str:
        """Export products to CSV format"""
        import csv
        import io
        
        products = self.get_all_products()
        if not products:
            return ""
        
        output = io.StringIO()
        fieldnames = ['id', 'name', 'description', 'price', 'stock_quantity', 'category', 'sku']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        
        writer.writeheader()
        for product in products:
            writer.writerow({k: product.get(k, '') for k in fieldnames})
        
        return output.getvalue()
    
    def import_products_from_csv(self, csv_content: str) -> tuple:
        """Import products from CSV content. Returns (success_count, error_messages)"""
        import csv
        import io
        
        success_count = 0
        errors = []
        
        try:
            csv_file = io.StringIO(csv_content)
            reader = csv.DictReader(csv_file)
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    name = row.get('name', '').strip()
                    description = row.get('description', '').strip()
                    price = float(row.get('price', 0))
                    stock = int(row.get('stock_quantity', 0))
                    category = row.get('category', '').strip() or None
                    sku = row.get('sku', '').strip() or None
                    
                    if not name or price <= 0:
                        errors.append(f"Row {row_num}: Invalid name or price")
                        continue
                    
                    self.add_product(name, description, price, stock, category, sku)
                    success_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
            
            return success_count, errors
            
        except Exception as e:
            return 0, [f"CSV parsing error: {str(e)}"]
