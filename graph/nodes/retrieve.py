# graph/nodes/retrieve.py
from langchain_postgres import PGVector
from langchain_ollama import OllamaEmbeddings
from graph.state import GraphState
import os
from dotenv import load_dotenv

load_dotenv()


def retrieve_documents_node(state: GraphState) -> GraphState:
    """Retrieve documents from PGVector"""
    print("🗂️ Retrieving documents...")

    question = state["question"]

    try:
        # Create retriever locally to avoid circular import
        embeddings = OllamaEmbeddings(
            model="nomic-embed-text",  # or "all-minilm" or other embedding models
            base_url="http://localhost:11434"  # default Ollama URL
        )
        vectorstore = PGVector(
            embeddings=embeddings,
            collection_name=os.getenv("COLLECTION_NAME", "telecom_docs"),
            connection=os.getenv("POSTGRES_CONNECTION"),
            use_jsonb=True,
        )

        retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
        documents = retriever.invoke(question)

        print(f"📄 Retrieved {len(documents)} documents")
        return {**state, "documents": documents}

    except Exception as e:
        print(f"❌ Error retrieving documents: {e}")
        # Return empty documents instead of failing
        return {**state, "documents": []}


# Export for your existing import pattern
retrieve = retrieve_documents_node