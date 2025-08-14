# from typing import Any, Dict

from graph.chains.generation_chain import generation_chain
from graph.state import GraphState


def generate(state: GraphState) -> GraphState: #Dict[str, Any]:
    print("---GENERATE---")
    question = state["question"]
    documents = state["relevant_documents"]  # Use relevant_documents instead of documents

    generation = generation_chain.invoke({"context": documents, "question": question})
    return {"question": question, "generation": generation}