from graph.chains.answer_grader import answer_grader
from graph.memory.memory_nodes import with_memory
from graph.state import GraphState


@with_memory  # Add this decorator
def grade_answer_node(state: GraphState) -> GraphState:
    """Grade the generated answer quality."""
    print("📊 Grading answer quality...")

    question = state["question"]
    generation = state["generation"]
    retry_count = state.get("retry_count", 0)

    try:
        grade_result = answer_grader.invoke({
            "question": question,
            "generation": generation
        })

        is_good = grade_result.binary_score.lower() == "yes"  # Convert string to bool
        print(f"Answer grade: {'✅ Good' if is_good else '❌ Needs improvement'}")

        # If answer is bad and we haven't retried too much, mark for retry
        if not is_good and retry_count < 2:  # Allow max 2 retries
            print(f"🔄 Answer needs improvement, retry #{retry_count + 1}")
            return {
                **state,
                "answer_grade": False,
                "needs_retry": True,
                "retry_count": retry_count + 1
            }

            # Answer is good OR we've tried enough times
        return {
            **state,
            "answer_grade": is_good,
            "needs_retry": False
        }

    except Exception as e:
        print(f"❌ Error grading answer: {e}")
        return {**state, "answer_grade": True, "needs_retry": False}  # Default to good on error