from graph.chains.answer_grader import answer_grader
from graph.memory.memory_nodes import with_memory
from graph.state import GraphState


@with_memory  # Add this decorator
def grade_answer_node(state: GraphState) -> GraphState:
    """Grade the generated answer quality."""
    print("📊 Grading answer quality...")

    question = state["question"]
    generation = state["generation"]

    try:
        grade_result = answer_grader.invoke({
            "question": question,
            "generation": generation
        })

        is_good = grade_result.binary_score.lower() == "yes"  # Convert string to bool
        print(f"Answer grade: {'✅ Good' if is_good else '❌ Needs improvement'}")

        return {**state, "answer_grade": is_good}

    except Exception as e:
        print(f"❌ Error grading answer: {e}")
        return {**state, "answer_grade": True}  # Default to good on error