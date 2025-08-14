"""
Memory management module for telecom call center conversations
"""

from .redis_client import redis_memory, RedisMemoryManager
from .memory_nodes import (
    with_memory,
    add_user_message,
    add_assistant_message,
    get_conversation_summary,
    extract_phone_from_memory,
    MemoryContext
)

__all__ = [
    'redis_memory',
    'RedisMemoryManager',
    'with_memory',
    'add_user_message',
    'add_assistant_message',
    'get_conversation_summary',
    'extract_phone_from_memory',
    'MemoryContext'
]