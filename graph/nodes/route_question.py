from graph.chains.router import question_router
from graph.state import GraphState


def route_question_node(state: GraphState) -> GraphState:
    """Route question to vectorstore or function calls."""
    print("🎯 Routing question...")

    question = state["question"]

    try:
        route_result = question_router.invoke({"question": question})
        datasource = route_result.datasource

        print(f"Question: '{question[:50]}...'")
        print(f"Route: {datasource}")

        return {
            **state,
            "datasource": datasource,
            "needs_function_call": datasource == "function_calls"
        }

    except Exception as e:
        print(f"❌ Error routing question: {e}")
        return {**state, "datasource": "vectorstore"}