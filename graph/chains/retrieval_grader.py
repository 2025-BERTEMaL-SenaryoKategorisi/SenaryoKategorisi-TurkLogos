from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_postgres import PGVector

# Initialize LLM (using Groq as in your previous examples)
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0
)


# Pydantic model for grading
class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents from pgvector."""

    binary_score: str = Field(
        description="Document is relevant to the question, 'yes' or 'no'"
    )
    confidence: str = Field(
        description="Confidence level: 'high', 'medium', or 'low'",
        default="medium"
    )


# Create structured LLM grader
structured_llm_grader = llm.with_structured_output(GradeDocuments)

# Optimized system prompt for pgvector results
system = """You are a document relevance grader for a RAG system using pgvector similarity search.

Your task is to assess whether a retrieved document is relevant to answer the user's question.

GRADING CRITERIA:
- Grade 'yes' if the document contains information that helps answer the question
- Grade 'yes' if the document has semantic relevance even without exact keywords
- Grade 'no' if the document is completely unrelated to the question
- Grade 'no' if the document is too generic or doesn't provide useful information

CONFIDENCE LEVELS:
- 'high': Document directly answers the question or contains highly relevant information
- 'medium': Document is related but may not fully answer the question
- 'low': Document has minimal relevance but some connection exists

Be practical - pgvector retrieval is based on semantic similarity, so focus on meaning over exact keyword matches."""

# Create the grading prompt
grade_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "Retrieved document: \n\n {document} \n\n User question: {question}"),
    ]
)

# Create the grader chain
retrieval_grader = grade_prompt | structured_llm_grader