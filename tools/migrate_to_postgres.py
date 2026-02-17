import json
import os
import psycopg2
from psycopg2.extras import execute_values
import numpy as np

def migrate():
    print("🚀 Starting Migration to PostgreSQL...")
    
    # DB Connection (using env or default)
    db_url = os.getenv("DATABASE_URL", "postgresql://xocoa:xocoa@localhost:5432/xocoadb")
    
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # 1. Enable pgvector
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        # 2. Create Tables
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chocolates (
                id SERIAL PRIMARY KEY,
                brand TEXT,
                name TEXT,
                cocoa_percentage FLOAT,
                maker_country TEXT,
                flavor_notes_primary TEXT,
                flavor_notes_secondary TEXT,
                price_retail FLOAT,
                price_currency TEXT,
                rating FLOAT,
                maker_website TEXT,
                embedding vector(768)
            );
        """)
        
        # 3. Load Data
        print(">>> Loading JSON files...")
        with open("data/chocolates.json", "r", encoding="utf-8") as f:
            chocolates = json.load(f)
            
        with open("data/chocolate_embeddings.json", "r", encoding="utf-8") as f:
            embeddings_list = json.load(f)
            id_to_embedding = {int(r["id"]): r["embedding"] for r in embeddings_list}

        # 4. Prepare for Insertion
        print(f">>> Preparing {len(chocolates)} records...")
        insert_data = []
        for p in chocolates:
            pid = int(p.get("id"))
            embedding = id_to_embedding.get(pid)
            
            insert_data.append((
                pid,
                p.get("brand"),
                p.get("name"),
                p.get("cocoa_percentage"),
                p.get("maker_country"),
                p.get("flavor_notes_primary"),
                p.get("flavor_notes_secondary"),
                p.get("price_retail"),
                p.get("price_currency", "USD"),
                p.get("rating"),
                p.get("maker_website"),
                embedding
            ))

        # 5. Insert (with UPSERT logic)
        execute_values(cur, """
            INSERT INTO chocolates (
                id, brand, name, cocoa_percentage, maker_country, 
                flavor_notes_primary, flavor_notes_secondary, price_retail, 
                price_currency, rating, maker_website, embedding
            ) VALUES %s
            ON CONFLICT (id) DO UPDATE SET
                brand = EXCLUDED.brand,
                name = EXCLUDED.name,
                cocoa_percentage = EXCLUDED.cocoa_percentage,
                embedding = EXCLUDED.embedding;
        """, insert_data)
        
        # 6. Create HNSW index for fast semantic search
        print(">>> Creating HNSW index for vector search...")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_chocolates_embedding ON chocolates USING hnsw (embedding vector_cosine_ops);")

        conn.commit()
        cur.close()
        conn.close()
        print("✅ Migration Successful!")

    except Exception as e:
        print(f"❌ Migration Failed: {e}")

if __name__ == "__main__":
    migrate()
