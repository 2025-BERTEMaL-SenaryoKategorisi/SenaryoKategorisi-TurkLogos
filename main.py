# main.py - with Redis memory
from graph.graph import create_telecom_workflow
from graph.state import GraphState
from graph.memory.redis_client import redis_memory
import uuid


def create_initial_state(question: str, conversation_id: str = None) -> GraphState:
    """Create initial state with Redis conversation ID"""
    if not conversation_id:
        conversation_id = str(uuid.uuid4())

    return {
        "question": question,
        "conversation_id": conversation_id,
        "generation": "",
        "documents": [],
        "relevant_documents": [],
        "tool_results": None,
        "datasource": "",
        "needs_function_call": False,
        "question_grade": False,
        "retrieval_grade": False,
        "answer_grade": False,
        "retry_count": 0,
        "conversation_history": [],
        "user_context": {}
    }


def test_redis_conversation():
    """Test conversation with Redis memory"""

    # Health check
    if not redis_memory.health_check():
        print("❌ Redis is not available")
        return

    app = create_telecom_workflow()
    conversation_id = "test_conv_redis_001"

    questions = [
        "Merhaba, nasılsınız?",
        "Benim paketim nedir? 0555 123 45 67",
        "Faturamı da görebilir miyim?",  # Should use cached phone
        "Teşekkürler!"
    ]

    for i, question in enumerate(questions):
        print(f"\n{'=' * 60}")
        print(f"🗣️ Turn {i + 1}: {question}")
        print('=' * 60)

        initial_state = create_initial_state(question, conversation_id)

        try:
            result = app.invoke(initial_state)

            print(f"✅ Assistant: {result.get('generation', 'No answer')}")

            # Check Redis memory
            history = redis_memory.get_conversation_history(conversation_id)
            phone = redis_memory.get_phone_from_conversation(conversation_id)

            print(f"💾 Redis - History length: {len(history)}")
            print(f"📱 Redis - Cached phone: {phone}")

        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_redis_conversation()