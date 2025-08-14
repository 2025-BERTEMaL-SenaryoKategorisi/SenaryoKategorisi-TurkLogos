"""
Redis-based memory manager for conversation history and user context
"""

import redis
import json
import os
from typing import Dict, Any, Optional, List
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class RedisMemoryManager:
    """Redis-based memory manager for telecom call center conversations"""

    def __init__(self):
        """Initialize Redis connection with environment variables"""
        try:
            self.redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                password=os.getenv('REDIS_PASSWORD', None),
                db=int(os.getenv('REDIS_DB', 0)),
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )

            # Test connection
            self.redis_client.ping()
            print("✅ Redis connected successfully")

        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            self.redis_client = None

        # TTL settings
        self.conversation_ttl = timedelta(hours=24)  # Conversations expire after 24 hours
        self.user_context_ttl = timedelta(days=30)  # User context expires after 30 days
        self.api_cache_ttl = timedelta(minutes=5)  # API responses cached for 5 minutes

    def _get_conversation_key(self, conversation_id: str) -> str:
        """Generate Redis key for conversation history"""
        return f"telecom:conversation:{conversation_id}"

    def _get_user_context_key(self, phone_number: str) -> str:
        """Generate Redis key for user context"""
        # Clean phone number for key
        clean_phone = phone_number.replace('+', '').replace(' ', '').replace('-', '')
        return f"telecom:user_context:{clean_phone}"

    def _get_phone_mapping_key(self, conversation_id: str) -> str:
        """Generate Redis key for conversation -> phone mapping"""
        return f"telecom:phone_mapping:{conversation_id}"

    def _get_api_cache_key(self, cache_key: str) -> str:
        """Generate Redis key for API response caching"""
        return f"telecom:api_cache:{cache_key}"

    def health_check(self) -> bool:
        """Check if Redis is available and responding"""
        try:
            if self.redis_client is None:
                return False
            self.redis_client.ping()
            return True
        except:
            return False

    # ========================================================================
    # CONVERSATION HISTORY METHODS
    # ========================================================================

    def save_conversation_history(self, conversation_id: str, history: List[Dict[str, str]]) -> bool:
        """
        Save conversation history to Redis

        Args:
            conversation_id: Unique conversation identifier
            history: List of message dictionaries with 'role' and 'content'

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.health_check():
            print("⚠️ Redis not available - conversation not saved")
            return False

        try:
            key = self._get_conversation_key(conversation_id)
            serialized_history = json.dumps(history, ensure_ascii=False)

            # Save with expiration
            self.redis_client.setex(
                key,
                self.conversation_ttl,
                serialized_history
            )

            print(f"💾 Saved conversation history: {len(history)} messages")
            return True

        except Exception as e:
            print(f"❌ Error saving conversation history: {e}")
            return False

    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, str]]:
        """
        Get conversation history from Redis

        Args:
            conversation_id: Unique conversation identifier

        Returns:
            List of message dictionaries, empty list if not found
        """
        if not self.health_check():
            return []

        try:
            key = self._get_conversation_key(conversation_id)
            serialized_history = self.redis_client.get(key)

            if serialized_history:
                history = json.loads(serialized_history)
                print(f"📚 Retrieved conversation history: {len(history)} messages")
                return history

            print("📭 No conversation history found")
            return []

        except Exception as e:
            print(f"❌ Error getting conversation history: {e}")
            return []

    def add_message_to_conversation(self, conversation_id: str, role: str, content: str) -> bool:
        """
        Add a single message to conversation history

        Args:
            conversation_id: Unique conversation identifier
            role: Message role ('user' or 'assistant')
            content: Message content

        Returns:
            bool: True if successful
        """
        if not self.health_check():
            return False

        try:
            # Get current history
            current_history = self.get_conversation_history(conversation_id)

            # Add new message
            new_message = {"role": role, "content": content}
            current_history.append(new_message)

            # Keep only last 20 messages to prevent memory bloat
            if len(current_history) > 20:
                current_history = current_history[-20:]
                print("🗑️ Trimmed conversation history to last 20 messages")

            # Save updated history
            return self.save_conversation_history(conversation_id, current_history)

        except Exception as e:
            print(f"❌ Error adding message to conversation: {e}")
            return False

    def clear_conversation(self, conversation_id: str) -> bool:
        """
        Clear conversation history and related data

        Args:
            conversation_id: Unique conversation identifier

        Returns:
            bool: True if successful
        """
        if not self.health_check():
            return False

        try:
            conv_key = self._get_conversation_key(conversation_id)
            phone_key = self._get_phone_mapping_key(conversation_id)

            # Delete keys
            deleted_count = self.redis_client.delete(conv_key, phone_key)

            print(f"🗑️ Cleared conversation data: {deleted_count} keys deleted")
            return True

        except Exception as e:
            print(f"❌ Error clearing conversation: {e}")
            return False

    # ========================================================================
    # USER CONTEXT METHODS
    # ========================================================================

    def save_user_context(self, phone_number: str, context: Dict[str, Any]) -> bool:
        """
        Save user context to Redis

        Args:
            phone_number: User's phone number
            context: Dictionary containing user context data

        Returns:
            bool: True if successful
        """
        if not self.health_check():
            return False

        try:
            key = self._get_user_context_key(phone_number)

            # Add metadata
            context_with_meta = {
                **context,
                "phone_number": phone_number,
                "last_updated": str(int(time.time())),
                "update_count": context.get("update_count", 0) + 1
            }

            serialized_context = json.dumps(context_with_meta, ensure_ascii=False)

            # Save with expiration
            self.redis_client.setex(
                key,
                self.user_context_ttl,
                serialized_context
            )

            print(f"💾 Saved user context for {phone_number}")
            return True

        except Exception as e:
            print(f"❌ Error saving user context: {e}")
            return False

    def get_user_context(self, phone_number: str) -> Dict[str, Any]:
        """
        Get user context from Redis

        Args:
            phone_number: User's phone number

        Returns:
            Dictionary containing user context, empty dict if not found
        """
        if not self.health_check():
            return {}

        try:
            key = self._get_user_context_key(phone_number)
            serialized_context = self.redis_client.get(key)

            if serialized_context:
                context = json.loads(serialized_context)
                print(f"👤 Retrieved user context for {phone_number}")
                return context

            print(f"👤 No user context found for {phone_number}")
            return {}

        except Exception as e:
            print(f"❌ Error getting user context: {e}")
            return {}

    def update_user_context(self, phone_number: str, updates: Dict[str, Any]) -> bool:
        """
        Update specific fields in user context

        Args:
            phone_number: User's phone number
            updates: Dictionary of fields to update

        Returns:
            bool: True if successful
        """
        try:
            current_context = self.get_user_context(phone_number)
            current_context.update(updates)
            return self.save_user_context(phone_number, current_context)

        except Exception as e:
            print(f"❌ Error updating user context: {e}")
            return False

    # ========================================================================
    # PHONE NUMBER MAPPING METHODS
    # ========================================================================

    def link_conversation_to_phone(self, conversation_id: str, phone_number: str) -> bool:
        """
        Link conversation ID to phone number for easy lookup

        Args:
            conversation_id: Unique conversation identifier
            phone_number: User's phone number

        Returns:
            bool: True if successful
        """
        if not self.health_check():
            return False

        try:
            key = self._get_phone_mapping_key(conversation_id)

            # Save mapping with same TTL as conversation
            self.redis_client.setex(key, self.conversation_ttl, phone_number)

            print(f"🔗 Linked conversation {conversation_id[:8]}... to {phone_number}")
            return True

        except Exception as e:
            print(f"❌ Error linking conversation to phone: {e}")
            return False

    def get_phone_from_conversation(self, conversation_id: str) -> Optional[str]:
        """
        Get phone number associated with conversation

        Args:
            conversation_id: Unique conversation identifier

        Returns:
            Phone number if found, None otherwise
        """
        if not self.health_check():
            return None

        try:
            key = self._get_phone_mapping_key(conversation_id)
            phone_number = self.redis_client.get(key)

            if phone_number:
                print(f"📞 Found phone {phone_number} for conversation {conversation_id[:8]}...")

            return phone_number

        except Exception as e:
            print(f"❌ Error getting phone from conversation: {e}")
            return None

    # ========================================================================
    # API RESPONSE CACHING METHODS
    # ========================================================================

    def cache_api_response(self, cache_key: str, response_data: Dict[str, Any], ttl_minutes: int = 5) -> bool:
        """
        Cache API responses to reduce external API calls

        Args:
            cache_key: Unique key for the cached response
            response_data: API response data to cache
            ttl_minutes: Time to live in minutes

        Returns:
            bool: True if successful
        """
        if not self.health_check():
            return False

        try:
            key = self._get_api_cache_key(cache_key)
            serialized_data = json.dumps(response_data, ensure_ascii=False)

            # Cache with TTL
            self.redis_client.setex(
                key,
                timedelta(minutes=ttl_minutes),
                serialized_data
            )

            print(f"💾 Cached API response: {cache_key}")
            return True

        except Exception as e:
            print(f"❌ Error caching API response: {e}")
            return False

    def get_cached_api_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Get cached API response

        Args:
            cache_key: Unique key for the cached response

        Returns:
            Cached response data if found, None otherwise
        """
        if not self.health_check():
            return None

        try:
            key = self._get_api_cache_key(cache_key)
            cached_data = self.redis_client.get(key)

            if cached_data:
                print(f"💾 Using cached API response: {cache_key}")
                return json.loads(cached_data)

            return None

        except Exception as e:
            print(f"❌ Error getting cached API response: {e}")
            return None

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """
        Get Redis memory usage statistics

        Returns:
            Dictionary with statistics
        """
        if not self.health_check():
            return {"error": "Redis not available"}

        try:
            # Get key counts
            conversation_keys = len(self.redis_client.keys("telecom:conversation:*"))
            user_context_keys = len(self.redis_client.keys("telecom:user_context:*"))
            phone_mapping_keys = len(self.redis_client.keys("telecom:phone_mapping:*"))
            api_cache_keys = len(self.redis_client.keys("telecom:api_cache:*"))

            # Get Redis info
            info = self.redis_client.info()

            return {
                "redis_status": "connected",
                "key_counts": {
                    "conversations": conversation_keys,
                    "user_contexts": user_context_keys,
                    "phone_mappings": phone_mapping_keys,
                    "api_cache": api_cache_keys
                },
                "memory_usage": {
                    "used_memory": info.get("used_memory_human", "Unknown"),
                    "total_keys": info.get("db0", {}).get("keys", 0) if "db0" in info else 0
                }
            }

        except Exception as e:
            return {"error": str(e)}

    def cleanup_expired_keys(self) -> int:
        """
        Manually cleanup expired keys (Redis does this automatically, but this is for debugging)

        Returns:
            Number of keys cleaned up
        """
        if not self.health_check():
            return 0

        try:
            # Find keys without TTL (shouldn't happen, but just in case)
            all_keys = self.redis_client.keys("telecom:*")
            keys_without_ttl = []

            for key in all_keys:
                ttl = self.redis_client.ttl(key)
                if ttl == -1:  # No expiration set
                    keys_without_ttl.append(key)

            # You could delete these or set TTL
            print(f"🔍 Found {len(keys_without_ttl)} keys without TTL")

            return len(keys_without_ttl)

        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
            return 0


# Import time for timestamps
import time

# Global Redis manager instance
redis_memory = RedisMemoryManager()