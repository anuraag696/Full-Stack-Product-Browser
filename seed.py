import os
import psycopg2
from psycopg2.extras import execute_values
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

CATEGORIES = ["Electronics", "Clothing", "Home & Kitchen", "Books", "Beauty", "Sports"]
PRODUCT_NAMES = ["UltraSmart Phone", "EcoWear T-Shirt", "ProCook Pan", "Shadow Novel", "Glow Serum", "Aero Fit Shoes"]

def generate_mock_products(count=200000):
    print(f"Generating {count} products in memory...")
    data = []
    base_time = datetime.now()
    
    for i in range(count):
        name = f"{random.choice(PRODUCT_NAMES)} {random.randint(100, 999)}"
        category = random.choice(CATEGORIES)
        price = round(random.uniform(9.99, 1499.99), 2)
        created_at = base_time - timedelta(seconds=i * 5)
        updated_at = created_at
        
        data.append((name, category, price, created_at, updated_at))
    return data

def seed_database():
    products = generate_mock_products(200000)
    
    # Direct IPv6 endpoint matching your hotspot, using the transaction port
    DB_URI = "postgresql://postgres:Anuraag%402004@db.iilajlduyjyeibazlyl.supabase.co:6543/postgres"
    
    conn = psycopg2.connect(DB_URI)
    cursor = conn.cursor()
    # ... rest of your code
    
    # Create table and critical composite indexes if they don't exist
    setup_sql = """
    CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        category VARCHAR(100) NOT NULL,
        price NUMERIC(10, 2) NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_products_pagination ON products (created_at DESC, id DESC);
    CREATE INDEX IF NOT EXISTS idx_products_category_pagination ON products (category, created_at DESC, id DESC);
    """
    
    try:
        print("Setting up table and indexes...")
        cursor.execute(setup_sql)
        conn.commit()

        print("Executing bulk insertion into database (this will take 2-3 seconds)...")
        query = "INSERT INTO products (name, category, price, created_at, updated_at) VALUES %s"
        execute_values(cursor, query, products, page_size=20000)
        conn.commit()
        print("Database seeded successfully with 200,000 products!")
    except Exception as e:
        conn.rollback()
        print(f"Error during seeding: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    seed_database()