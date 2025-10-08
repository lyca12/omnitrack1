import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
import threading
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("❌ DATABASE_URL is not set. Please check your .env file.")
        
        self.lock = threading.Lock()
        self.init_database()
        self.create_demo_data()
    
    def get_connection(self):
        """Create a new database connection"""
        return psycopg2.connect(self.database_url)
    
    def init_database(self):
        """Initialize all required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL DEFAULT 'customer',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shopping_cart (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reserved_inventory (
                id SERIAL PRIMARY KEY,
                product_id INTEGER NOT NULL,
                username VARCHAR(255) NOT NULL,
                quantity INTEGER NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()
        print("✅ Database tables initialized successfully.")

    def create_demo_data(self):
        """Insert demo products only if the table is empty"""
        if not self.get_all_products():
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

            for p in demo_products:
                self.add_product(*p)
            print("✅ Demo data inserted successfully.")

    def add_product(self, name, description, price, stock, category, sku):
        """Add a single product"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO products (name, description, price, stock_quantity, category, sku)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (name, description, price, stock, category, sku))
            conn.commit()
            conn.close()

    def get_all_products(self) -> List[Dict]:
        """Return all products"""
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM products ORDER BY name")
        rows = cursor.fetchall()
        conn.close()
        return rows

# Run this file directly to test
if __name__ == "__main__":
    db = DatabaseManager()
    products = db.get_all_products()
    print(f"✅ {len(products)} products in the database.")
