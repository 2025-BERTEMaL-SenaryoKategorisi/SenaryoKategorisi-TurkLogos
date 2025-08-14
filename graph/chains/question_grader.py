from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
# from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv(verbose=True)

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0
)

class GradeQuestions(BaseModel):
    """Binary score for relevance check on user question about Turkish Telecom Call Center"""

    binary_score: str = Field(
        description="Questions are relevant to the question, 'yes' or 'no'"
    )

structured_llm_grader = llm.with_structured_output(GradeQuestions)

system = """You are a question relevance grader for a Turkish telecom call center (like Turkcell or Vodafone).

Grade 'yes' if the question is:
- Related to telecom services (packages, billing, usage, technical support)
- A greeting or polite conversation starter
- Clear and understandable (even with typos or informal language)
- Something a call center agent could reasonably help with

Grade 'no' if the question is:
- Completely unrelated to telecom services
- Gibberish, random text, or meaningless
- About topics like general knowledge, other industries, or academic subjects
- Empty or contains only special characters

Examples:
- "Benim paketim nedir?" → 'yes' (telecom related)
- "Merhaba, nasılsınız?" → 'yes' (polite greeting)
- "LLM'ler neden gelişmiş?" → 'no' (unrelated to telecom)
- "asdfgh" → 'no' (gibberish)
- "5 + 5 kaç eder ?" -> 'no' (unrelated to telecom)

Be practical - focus on whether a telecom call center agent could help with this question."""

grade_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "Grade question: \n\n User question: {question}"),
    ]
)

question_grader = grade_prompt | structured_llm_grader


