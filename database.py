# database.py

import os
import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import threading
from typing import List, Dict
import pandas as pd

# --- Database URL Helper ---
# This function makes the code work seamlessly in both local and deployed environments.
def get_database_url():
    """
    Gets the database URL.
    Checks for Streamlit secrets first (for deployment), 
    then falls back to a local .env file (for local development).
    """
    # Check if running on Streamlit Cloud and the secret is set
    if hasattr(st, 'secrets') and 'DATABASE_URL' in st.secrets:
        print("✅ Found DATABASE_URL in Streamlit secrets.")
        return st.secrets['DATABASE_URL']
    
    # Fallback for local development
    print("ℹ️ Looking for DATABASE_URL in local .env file.")
    load_dotenv()
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        print("✅ Found DATABASE_URL in .env file.")
    return db_url

# --- Main Database Class ---
class DatabaseManager:
    def __init__(self):
        """Initializes the connection and sets up the database."""
        self.database_url = get_database_url()
        if not self.database_url:
            raise ValueError("❌ DATABASE_URL not found. Check Streamlit secrets or local .env file.")
        
        self.lock = threading.Lock()
        try:
            self.init_database()
            self.create_demo_data()
        except psycopg2.OperationalError as e:
            print("❌ DATABASE CONNECTION FAILED. Check network rules in Supabase and verify the URL.")
            raise e

    def get_connection(self):
        """Creates a new database connection."""
        return psycopg2.connect(self.database_url)

    def init_database(self):
        """Initializes all required tables if they don't exist."""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                # Users Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(255) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        role VARCHAR(50) NOT NULL DEFAULT 'customer' CHECK(role IN ('admin', 'staff', 'customer'))
                    )
                """)
                # Products Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS products (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        price DECIMAL(10, 2) NOT NULL,
                        stock_quantity INTEGER NOT NULL DEFAULT 0,
                        category VARCHAR(100),
                        sku VARCHAR(100) UNIQUE
                    )
                """)
                # Orders Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS orders (
                        id SERIAL PRIMARY KEY,
                        customer_id INTEGER NOT NULL REFERENCES users(id),
                        status VARCHAR(50) NOT NULL DEFAULT 'Placed' CHECK(status IN ('Placed', 'Paid', 'Delivered', 'Cancelled')),
                        total_amount DECIMAL(10, 2) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
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
            ("Basketball", 29.99, 50, "Sports", "SPT-BB-001"),
            ("Soccer Ball", 24.99, 30, "Sports", "SPT-SB-002"),
            ("Tennis Racket", 89.99, 15, "Sports", "SPT-TR-003"),
            ("Running Shoes", 79.99, 25, "Footwear", "FTW-RS-004"),
            ("Gym Bag", 34.99, 40, "Accessories", "ACC-GB-005"),
            ("Water Bottle", 19.99, 100, "Accessories", "ACC-WB-006"),
            ("Yoga Mat", 39.99, 20, "Fitness", "FIT-YM-007"),
            ("Cricket Bat", 69.99, 8, "Sports", "SPT-CB-009"),
        ]
        added_count = 0
        for p in demo_products:
            if not self.get_product_by_sku(p[4]):
                self.add_product(*p)
                added_count += 1
        if added_count > 0:
            print(f"✅ {added_count} new demo products inserted.")

    def add_product(self, name, price, stock, category, sku):
        """Adds a single product."""
        with self.lock:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO products (name, price, stock_quantity, category, sku)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (name, price, stock, category, sku))
    
    def get_all_products(self) -> pd.DataFrame:
        """Returns all products as a Pandas DataFrame."""
        with self.get_connection() as conn:
            df = pd.read_sql("SELECT id, name, category, price, stock_quantity FROM products ORDER BY name", conn)
            return df

# --- Auth Class (Simplified for this example) ---
# A full implementation would use st.session_state and more complex logic
class AuthManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def login(self, username, password):
        """A placeholder for login logic."""
        # In a real app, you would query the 'users' table and check a hashed password.
        if username == "admin" and password == "admin":
            return {"username": "admin", "role": "admin"}
        if username == "customer" and password == "customer":
            return {"username": "customer", "role": "customer", "id": 1} # Dummy ID
        return None

