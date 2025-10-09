# database.py
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import threading
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("❌ DATABASE_URL is not set. Please check your .env and docker-compose.yml files.")
        
        # Use a lock for thread safety, which is good practice
        self.lock = threading.Lock()
        self.init_database()
        self.create_demo_data()
    
    def get_connection(self):
        """Creates a new database connection."""
        try:
            return psycopg2.connect(self.database_url)
        except psycopg2.OperationalError as e:
            print("❌ Could not connect to the database. Is Docker running? Is the DATABASE_URL correct?")
            raise e
    
    def init_database(self):
        """Initializes all required tables if they don't exist."""
        # This structure ensures the connection is always closed
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                # Users Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(255) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        role VARCHAR(50) NOT NULL DEFAULT 'customer',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                # Products Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS products (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        description TEXT,
                        price DECIMAL(10, 2) NOT NULL,
                        stock_quantity INTEGER NOT NULL DEFAULT 0,
                        category VARCHAR(100),
                        sku VARCHAR(100) UNIQUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                # ... (add other CREATE TABLE statements here: orders, order_items, etc.) ...
        print("✅ Database tables checked/initialized successfully.")

    def get_product_by_sku(self, sku):
        """Checks if a product with a given SKU exists."""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT id FROM products WHERE sku = %s", (sku,))
                return cursor.fetchone()

    def create_demo_data(self):
        """Inserts demo products only if they don't already exist."""
        demo_products = [
            ("Basketball", "Professional basketball", 29.99, 50, "Sports", "SPT-BB-001"),
            ("Soccer Ball", "FIFA approved soccer ball", 24.99, 30, "Sports", "SPT-SB-002"),
            ("Tennis Racket", "Professional tennis racket", 89.99, 15, "Sports", "SPT-TR-003"),
            ("Running Shoes", "Comfortable running shoes", 79.99, 25, "Footwear", "FTW-RS-004"),
            ("Gym Bag", "Large sports gym bag", 34.99, 40, "Accessories", "ACC-GB-005"),
        ]

        added_count = 0
        for p in demo_products:
            # Check if product with this SKU already exists to prevent duplicates
            if not self.get_product_by_sku(p[5]):
                self.add_product(*p)
                added_count += 1
        
        if added_count > 0:
            print(f"✅ {added_count} new demo products inserted successfully.")

    def add_product(self, name, description, price, stock, category, sku):
        """Adds a single product."""
        with self.lock:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO products (name, description, price, stock_quantity, category, sku)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (name, description, price, stock, category, sku))
    
    def get_all_products(self) -> List[Dict]:
        """Returns all products."""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM products ORDER BY name")
                return cursor.fetchall()

# This block allows you to run `python database.py` to test the connection and setup
if __name__ == "__main__":
    try:
        db = DatabaseManager()
        products = db.get_all_products()
        print(f"✅ Success! Found {len(products)} products in the database.")
        # Print a few products to verify
        for prod in products[:3]:
            print(f"  - {prod['name']} (${prod['price']})")
    except Exception as e:
        print(f"An error occurred during testing: {e}")

