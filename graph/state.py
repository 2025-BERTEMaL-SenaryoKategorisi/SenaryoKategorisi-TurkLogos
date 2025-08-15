from typing import List, TypedDict, Optional, Dict, Any
from langchain.schema import Document


class GraphState(TypedDict, total=False):
    """
    Represents the state of our telecom call center graph.
    """
    # Input
    question: str
    conversation_id: str
    # Routing
    datasource: str  # "vectorstore" or "function_calls"

    # Document retrieval
    documents: List[Document]
    relevant_documents: List[Document]

    conversation_history: List[Dict[str, str]]  # Loaded from Redis
    user_context: Dict[str, Any]  # Loaded from Redis

    # Tool/API results
    tool_results: Optional[Dict[str, Any]]

    # Generation
    generation: str

    # Grading
    question_grade: bool  # Is question relevant?
    retrieval_grade: bool  # Are docs relevant?
    answer_grade: bool  # Is answer good?

    # Control flow
    needs_function_call: bool
    retry_count: int
    needs_retry: bool


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