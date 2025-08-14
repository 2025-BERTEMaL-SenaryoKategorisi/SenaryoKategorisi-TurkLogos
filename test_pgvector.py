# test_pgvector.py
import os
from dotenv import load_dotenv
from langchain_postgres import PGVector
from langchain_ollama import OllamaEmbeddings
import psycopg2

load_dotenv()




def test_postgres_connection():
    """Test basic PostgreSQL connection"""
    try:
        conn = psycopg2.connect(os.getenv("POSTGRES_CONNECTION"))
        cursor = conn.cursor()

        # Test pgvector extension
        cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
        result = cursor.fetchone()

        if result:
            print("✅ PostgreSQL connected and pgvector extension is available")
        else:
            print("❌ pgvector extension not found")

        # Test collections
        cursor.execute("SELECT name FROM langchain_pg_collection;")
        collections = cursor.fetchall()
        print(f"📚 Available collections: {[c[0] for c in collections]}")

        # Test document count
        cursor.execute("SELECT COUNT(*) FROM langchain_pg_embedding;")
        doc_count = cursor.fetchone()[0]
        print(f"📄 Total documents: {doc_count}")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")


def test_pgvector_langchain():
    """Test PGVector with LangChain"""
    try:
        embeddings = OllamaEmbeddings(
            model="nomic-embed-text",  # or "all-minilm" or other embedding models
            base_url="http://localhost:11434"  # default Ollama URL
        )

        vectorstore = PGVector(
            embeddings=embeddings,
            collection_name=os.getenv("COLLECTION_NAME"),
            connection=os.getenv("POSTGRES_CONNECTION"),
            use_jsonb=True,
        )

        # Test similarity search
        results = vectorstore.similarity_search("paket fiyatları nedir", k=3)

        print("✅ PGVector LangChain integration working")
        print(f"📄 Found {len(results)} relevant documents:")

        for i, doc in enumerate(results, 1):
            print(f"  {i}. {doc.page_content[:100]}...")

    except Exception as e:
        print(f"❌ PGVector LangChain test failed: {e}")


def test_redis_connection():
    """Test Redis connection"""
    try:
        from graph.memory.redis_client import redis_memory

        if redis_memory.health_check():
            print("✅ Redis connected successfully")

            # Test basic operations
            redis_memory.redis_client.set("test_key", "test_value")
            value = redis_memory.redis_client.get("test_key")

            if value == "test_value":
                print("✅ Redis read/write test passed")

            redis_memory.redis_client.delete("test_key")
        else:
            print("❌ Redis connection failed")

    except Exception as e:
        print(f"❌ Redis test failed: {e}")


if __name__ == "__main__":
    print("=== Testing Database Connections ===\n")

    test_postgres_connection()
    print()
    test_pgvector_langchain()
    print()
    test_redis_connection()