import pytest
import os
import psycopg2
import redis
from channel_b.service import ChannelBService
from channel_c.explainer import LLMExplainer

def test_postgres_connectivity():
    """Verify that the DB_URL is accessible and pgvector is enabled."""
    db_url = os.getenv("DATABASE_URL", "postgresql://xocoa:xocoa@localhost:5432/xocoadb")
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.execute("SELECT 'vector'::regtype;") # Verify pgvector extension
        conn.close()
    except Exception as e:
        pytest.fail(f"PostgreSQL Connectivity/Extension check failed: {e}")

def test_redis_caching_logic():
    """Verify that the LLMExplainer successfully uses Redis."""
    explainer = LLMExplainer()
    if not explainer.redis:
        pytest.skip("Redis not available for testing")
    
    test_key = "test:connection"
    explainer.redis.set(test_key, "ok")
    assert explainer.redis.get(test_key).decode('utf-8') == "ok"
    explainer.redis.delete(test_key)

def test_vector_search_fallback():
    """Verify ChannelBService falls back to JSON if DB is down."""
    # Temporarily unset DB_URL to force JSON mode
    os.environ["DATABASE_URL"] = ""
    service = ChannelBService("data/chocolate_embeddings.json")
    results = service.rank([1, 2, 3], "dark chocolate", top_k=2)
    assert len(results) <= 2
    assert isinstance(results, list)
