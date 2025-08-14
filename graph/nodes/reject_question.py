from graph.state import GraphState
def reject_question_node(state: GraphState) -> GraphState:
    """Handle rejected questions."""
    print("❌ Question rejected")

    return {
        **state,
        "generation": "Üzgünüm, bu soruyu anlayamadım. Telecom hizmetlerimiz hakkında bir soru sorabilir misiniz?"
    }