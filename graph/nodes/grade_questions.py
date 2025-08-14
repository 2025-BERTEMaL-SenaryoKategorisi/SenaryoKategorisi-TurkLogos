from graph.chains.question_grader import question_grader
from graph.state import GraphState
from graph.memory.memory_nodes import with_memory


@with_memory  # Add this decorator
def grade_question_node(state: GraphState) -> GraphState:
    """Grade if the user question is relevant and answerable."""
    print("📝 Grading question relevance...")

    question = state["question"]
    conversation_history = state.get("conversation_history", [])

    # Add context from conversation history
    context = question
    if conversation_history:
        recent_history = conversation_history[-4:]
        history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_history])
        context = f"Previous conversation:\n{history_text}\n\nCurrent question: {question}"

    try:
        grade_result = question_grader.invoke({"question": context})
        is_relevant = grade_result.binary_score.lower() == "yes"

        print(f"Question: '{question[:50]}...'")
        print(f"Grade: {'✅ Relevant' if is_relevant else '❌ Not relevant'}")

        # Add user message to conversation history
        conversation_history = state.get("conversation_history", [])
        updated_history = conversation_history + [{"role": "user", "content": question}]

        return {
            **state,
            "question_grade": is_relevant,
            "conversation_history": updated_history  # This will be saved by @with_memory
        }

    except Exception as e:
        print(f"❌ Error grading question: {e}")
        return {**state, "question_grade": True}