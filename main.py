from graph.graph import create_telecom_workflow
from graph.state import GraphState


def create_initial_state(question: str) -> GraphState:
    """Create initial state with all required fields"""
    return {
        "question": question,
        "generation": "",
        "documents": [],
        "relevant_documents": [],
        "tool_results": None,
        "datasource": "",
        "needs_function_call": False,
        "question_grade": False,
        "retrieval_grade": False,
        "answer_grade": False,
        "retry_count": 0
    }


def test_workflow():
    """Test the complete workflow"""

    # Create workflow
    app = create_telecom_workflow()

    # Test questions
    test_questions = [
        "Benim paketim nedir?",  # Should go to function_calls
        "Şirket politikaları nelerdir ?",  # Should go to vectorstore
        "Merhaba, nasılsınız?",  # Should be accepted
        "LLM'ler neden gelişmiş?",  # Should be rejected
        "Faturamı görebilir miyim?",  # Should go to function_calls
    ]

    for question in test_questions:
        print(f"\n{'=' * 60}")
        print(f"🤖 Testing: {question}")
        print('=' * 60)

        # Create initial state
        initial_state = create_initial_state(question)

        try:
            # Run workflow
            result = app.invoke(initial_state)

            print(f"✅ Final Answer: {result.get('generation', 'No answer')}")
            print(f"📊 Route: {result.get('datasource', 'Unknown')}")
            print(f"🎯 Question Grade: {result.get('question_grade', 'Unknown')}")
            print(f"📈 Answer Grade: {result.get('answer_grade', 'Unknown')}")

        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_workflow()