# clear_cache.py
from graph.memory.redis_client import redis_memory

def clear_api_cache():
    """Clear all API cache"""
    try:
        keys = redis_memory.redis_client.keys("telecom:api_cache:*")
        if keys:
            deleted = redis_memory.redis_client.delete(*keys)
            print(f"🗑️ Cleared {deleted} cached API responses")
        else:
            print("ℹ️ No cached API responses found")
    except Exception as e:
        print(f"❌ Error clearing cache: {e}")

def clear_user_context(phone_number: str):
    """Clear specific user context"""
    try:
        key = f"telecom:user_context:{phone_number.replace('+', '').replace(' ', '').replace('-', '')}"
        deleted = redis_memory.redis_client.delete(key)
        print(f"🗑️ Cleared user context: {deleted} keys deleted")
    except Exception as e:
        print(f"❌ Error clearing user context: {e}")

if __name__ == "__main__":
    clear_api_cache()
    clear_user_context("+905551234567")
    print("✅ Cache cleared!")