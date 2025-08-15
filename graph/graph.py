# Import all nodes
from langgraph.graph import StateGraph
from typing import Literal

# Import your state
from graph.state import GraphState

# Import all nodes - fix this import
from graph.nodes.grade_questions import grade_question_node
from graph.nodes.route_question import route_question_node
from graph.nodes.retrieve import retrieve  # Change this line
from graph.nodes.grade_documents import grade_documents
from graph.nodes.function_calls import function_calls_node
from graph.nodes.generation import generate_answer_node, regenerate_answer_node
from graph.nodes.grade_answer import grade_answer_node
from graph.nodes.reject_question import reject_question_node

def create_telecom_workflow():
    """Create the complete telecom call center workflow"""

    workflow = StateGraph(GraphState)

    # Add all nodes
    workflow.add_node("grade_question", grade_question_node)
    workflow.add_node("route_question", route_question_node)
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("grade_documents", grade_documents)
    workflow.add_node("function_calls", function_calls_node)
    workflow.add_node("generate", generate_answer_node)
    workflow.add_node("regenerate", regenerate_answer_node)  # New retry node
    workflow.add_node("grade_answer", grade_answer_node)
    workflow.add_node("reject_question", reject_question_node)

    # Set entry point
    workflow.set_entry_point("grade_question")

    # Conditional edge functions
    def should_continue_after_question_grade(state: GraphState) -> Literal["route_question", "reject_question"]:
        if state.get("question_grade", False):
            return "route_question"
        else:
            return "reject_question"

    def route_after_routing(state: GraphState) -> Literal["retrieve", "function_calls"]:
        if state.get("datasource") == "vectorstore":
            return "retrieve"
        else:
            return "function_calls"

    def should_continue_after_retrieval_grade(state: GraphState) -> Literal["generate", "function_calls"]:
        if state.get("retrieval_grade", False) and state.get("relevant_documents"):
            return "generate"
        else:
            return "function_calls"

    def should_continue_after_answer_grade(state: GraphState) -> Literal["regenerate", "__end__"]:
        """After grading answer: retry if bad, end if good"""
        needs_retry = state.get("needs_retry", False)
        retry_count = state.get("retry_count", 0)
        answer_grade = state.get("answer_grade", False)

        print(f"🔍 Debug - needs_retry: {needs_retry}, retry_count: {retry_count}, answer_grade: {answer_grade}")

        if needs_retry and retry_count <3:
            return "regenerate"
        else:
            return "__end__"

    # Add conditional edges
    workflow.add_conditional_edges(
        "grade_question",
        should_continue_after_question_grade,
        {
            "route_question": "route_question",
            "reject_question": "reject_question"
        }
    )

    workflow.add_conditional_edges(
        "route_question",
        route_after_routing,
        {
            "retrieve": "retrieve",
            "function_calls": "function_calls"
        }
    )

    workflow.add_conditional_edges(
        "grade_documents",
        should_continue_after_retrieval_grade,
        {
            "generate": "generate",
            "function_calls": "function_calls"
        }
    )


    workflow.add_conditional_edges(
        "grade_answer",
        should_continue_after_answer_grade,
        {
            "regenerate": "regenerate",
            "__end__": "__end__"
        }
    )

    # Add simple edges
    workflow.add_edge("retrieve", "grade_documents")
    workflow.add_edge("function_calls", "generate")
    workflow.add_edge("generate", "grade_answer")
    workflow.add_edge("regenerate", "grade_answer")
    workflow.add_edge("reject_question", "__end__")

    return workflow.compile()