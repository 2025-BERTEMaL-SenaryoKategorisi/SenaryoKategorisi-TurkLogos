"""
Memory-aware node decorators and utilities for LangGraph workflow
"""

import uuid
from typing import Callable, Dict, Any
from functools import wraps
from graph.memory.redis_client import redis_memory
from graph.state import GraphState


def with_memory(node_func: Callable[[GraphState], GraphState]) -> Callable[[GraphState], GraphState]:
    """
    Decorator to add Redis memory functionality to any node function.

    This decorator:
    1. Loads conversation history and user context from Redis before node execution
    2. Ensures conversation_id exists
    3. Saves updated memory back to Redis after node execution

    Args:
        node_func: The original node function to wrap

    Returns:
        Memory-enhanced node function
    """

    @wraps(node_func)
    def memory_wrapper(state: GraphState) -> GraphState:
        print(f"🧠 Loading memory for node: {node_func.__name__}")

        # Ensure conversation_id exists
        conversation_id = state.get("conversation_id")
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            print(f"🆕 Generated new conversation ID: {conversation_id[:8]}...")
            state = {**state, "conversation_id": conversation_id}

        # Load conversation history from Redis
        conversation_history = redis_memory.get_conversation_history(conversation_id)

        # Try to get phone number from conversation mapping
        phone_number = redis_memory.get_phone_from_conversation(conversation_id)
        user_context = {}

        # Load user context if we have a phone number
        if phone_number:
            user_context = redis_memory.get_user_context(phone_number)
            print(f"👤 Loaded user context for {phone_number}")

        # Create memory-enhanced state
        memory_enhanced_state = {
            **state,
            "conversation_history": conversation_history,
            "user_context": user_context
        }

        print(f"📚 Loaded {len(conversation_history)} conversation messages")
        print(f"👤 Loaded {len(user_context)} user context fields")

        # Execute the original node function
        try:
            result_state = node_func(memory_enhanced_state)
        except Exception as e:
            print(f"❌ Error in node {node_func.__name__}: {e}")
            # Return original state with error info
            return {**memory_enhanced_state, "error": str(e)}

        # Save updated memory back to Redis
        _save_memory_updates(result_state, conversation_id, phone_number)

        return result_state

    return memory_wrapper


def _save_memory_updates(state: GraphState, conversation_id: str, original_phone: str = None):
    """
    Save memory updates back to Redis

    Args:
        state: Updated state from node execution
        conversation_id: Conversation identifier
        original_phone: Original phone number (if any)
    """
    try:
        # Save conversation history if updated
        if "conversation_history" in state:
            updated_history = state["conversation_history"]
            redis_memory.save_conversation_history(conversation_id, updated_history)

        # Determine phone number for user context saving
        phone_number = original_phone

        # Try to get phone from user context or other sources
        user_context = state.get("user_context", {})
        if not phone_number and "phone_number" in user_context:
            phone_number = user_context["phone_number"]

        # Save user context if we have a phone number and context updates
        if phone_number and user_context:
            redis_memory.save_user_context(phone_number, user_context)

            # Also update the conversation -> phone mapping
            redis_memory.link_conversation_to_phone(conversation_id, phone_number)

        print(f"💾 Memory updates saved for conversation {conversation_id[:8]}...")

    except Exception as e:
        print(f"❌ Error saving memory updates: {e}")


def add_user_message(conversation_id: str, message: str) -> bool:
    """
    Utility function to add a user message to conversation history

    Args:
        conversation_id: Conversation identifier
        message: User message content

    Returns:
        bool: True if successful
    """
    return redis_memory.add_message_to_conversation(conversation_id, "user", message)


def add_assistant_message(conversation_id: str, message: str) -> bool:
    """
    Utility function to add an assistant message to conversation history

    Args:
        conversation_id: Conversation identifier
        message: Assistant message content

    Returns:
        bool: True if successful
    """
    return redis_memory.add_message_to_conversation(conversation_id, "assistant", message)


def get_conversation_summary(conversation_id: str) -> Dict[str, Any]:
    """
    Get a summary of the conversation

    Args:
        conversation_id: Conversation identifier

    Returns:
        Dictionary with conversation summary
    """
    try:
        history = redis_memory.get_conversation_history(conversation_id)
        phone_number = redis_memory.get_phone_from_conversation(conversation_id)

        user_messages = [msg for msg in history if msg["role"] == "user"]
        assistant_messages = [msg for msg in history if msg["role"] == "assistant"]

        summary = {
            "conversation_id": conversation_id,
            "phone_number": phone_number,
            "total_messages": len(history),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "last_user_message": user_messages[-1]["content"] if user_messages else None,
            "last_assistant_message": assistant_messages[-1]["content"] if assistant_messages else None
        }

        return summary

    except Exception as e:
        return {"error": str(e)}


def extract_phone_from_memory(conversation_id: str, user_context: Dict[str, Any], conversation_history: list) -> str:
    """
    Extract phone number from various memory sources

    Args:
        conversation_id: Conversation identifier
        user_context: User context dictionary
        conversation_history: List of conversation messages

    Returns:
        Phone number if found, None otherwise
    """

    # Try conversation mapping first
    phone = redis_memory.get_phone_from_conversation(conversation_id)
    if phone:
        print(f"📞 Found phone in conversation mapping: {phone}")
        return phone

    # Try user context
    if "phone_number" in user_context:
        phone = user_context["phone_number"]
        print(f"📞 Found phone in user context: {phone}")
        return phone

    # Try conversation history
    for message in reversed(conversation_history):
        if message["role"] == "user":
            # You'll need to import your phone extraction function
            try:
                from graph.nodes.function_calls import extract_phone_number
                phone = extract_phone_number(message["content"])
                if phone:
                    print(f"📞 Found phone in conversation history: {phone}")
                    return phone
            except ImportError:
                # Fallback to simple regex
                import re
                phone_match = re.search(r'\+?9?0?5\d{9}', message["content"])
                if phone_match:
                    phone = phone_match.group(0)
                    if not phone.startswith('+'):
                        phone = '+90' + phone[-10:]
                    print(f"📞 Found phone in conversation history (regex): {phone}")
                    return phone

    return None


class MemoryContext:
    """
    Context manager for working with memory in nodes
    """

    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id
        self.conversation_history = []
        self.user_context = {}
        self.phone_number = None

    def __enter__(self):
        """Load memory on context entry"""
        self.conversation_history = redis_memory.get_conversation_history(self.conversation_id)
        self.phone_number = redis_memory.get_phone_from_conversation(self.conversation_id)

        if self.phone_number:
            self.user_context = redis_memory.get_user_context(self.phone_number)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Save memory on context exit"""
        if self.conversation_history:
            redis_memory.save_conversation_history(self.conversation_id, self.conversation_history)

        if self.phone_number and self.user_context:
            redis_memory.save_user_context(self.phone_number, self.user_context)
            redis_memory.link_conversation_to_phone(self.conversation_id, self.phone_number)

    def add_user_message(self, content: str):
        """Add user message to context"""
        self.conversation_history.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str):
        """Add assistant message to context"""
        self.conversation_history.append({"role": "assistant", "content": content})

    def set_phone_number(self, phone_number: str):
        """Set phone number and load user context"""
        self.phone_number = phone_number
        self.user_context = redis_memory.get_user_context(phone_number)

    def update_user_context(self, updates: Dict[str, Any]):
        """Update user context"""
        self.user_context.update(updates)


# Example usage function for testing
def test_memory_functions():
    """Test memory functionality"""

    print("🧪 Testing memory functions...")

    # Test conversation ID
    test_conv_id = str(uuid.uuid4())
    print(f"🆔 Test conversation ID: {test_conv_id}")

    # Test adding messages
    redis_memory.add_message_to_conversation(test_conv_id, "user", "Merhaba, benim paketim nedir? 0555 123 45 67")
    redis_memory.add_message_to_conversation(test_conv_id, "assistant", "Merhaba! Paket bilgilerinizi getiriyorum...")
    redis_memory.add_message_to_conversation(test_conv_id, "user", "Faturamı da görebilir miyim?")

    # Test phone linking
    redis_memory.link_conversation_to_phone(test_conv_id, "+905551234567")

    # Test user context
    redis_memory.save_user_context("+905551234567", {
        "name": "Test User",
        "package": "Gold",
        "last_login": "2024-01-15"
    })

    # Test retrieval
    history = redis_memory.get_conversation_history(test_conv_id)
    phone = redis_memory.get_phone_from_conversation(test_conv_id)
    context = redis_memory.get_user_context("+905551234567")

    print(f"📚 Retrieved {len(history)} messages")
    print(f"📞 Retrieved phone: {phone}")
    print(f"👤 Retrieved context: {context}")

    # Test memory context manager
    with MemoryContext(test_conv_id) as memory:
        print(f"🧠 Context manager loaded {len(memory.conversation_history)} messages")
        memory.add_assistant_message("İşte fatura bilgileriniz...")
        memory.update_user_context({"last_query": "bill_info"})

    print("✅ Memory test completed")


if __name__ == "__main__":
    test_memory_functions()