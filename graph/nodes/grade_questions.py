from graph.chains.question_grader import question_grader
from graph.state import GraphState
from graph.memory.memory_nodes import with_memory

@with_memory
def grade_question_node(state: GraphState) -> GraphState:
    """
    Grade if the user question is relevant and answerable.

    Args:
        state: Current graph state containing the question

    Returns:
        Updated state with question grade
    """
    print("📝 Grading question relevance...")

    question = state["question"]
    try:
        # Grade the question
        grade_result = question_grader.invoke({"question": question})

        # Convert string to boolean
        is_relevant = grade_result.binary_score.lower() == "yes"

        print(f"Question: '{question[:50]}...'")
        print(f"Grade: {'✅ Relevant' if is_relevant else '❌ Not relevant'}")

        return {
            **state,
            "question_grade": is_relevant  # Use string directly
        }

    except Exception as e:
        print(f"❌ Error grading question: {e}")
        return {
            **state,
            "question_grade": True  # Use string directly
        }