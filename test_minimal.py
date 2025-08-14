# test_minimal.py
from graph.nodes.grade_questions import grade_question_node
from graph.nodes.route_question import route_question_node

# Test individual nodes
test_state = {
    "question": "Benim paketim nedir?",
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

print("Testing question grader:")
result1 = grade_question_node(test_state)
print(f"Question grade: {result1['question_grade']}")

print("\nTesting router:")
result2 = route_question_node(result1)
print(f"Route: {result2['datasource']}")