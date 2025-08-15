from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0
)

class GradeAnswer(BaseModel):
    binary_score: str = Field(
        description="Answer addresses the question, 'yes' or 'no'"
    )
    reasoning: str = Field(
        description="Brief explanation of the grading decision"
    )

structured_llm_grader = llm.with_structured_output(GradeAnswer)

system = """You are a quality assessor for telecom call center responses. Your job is to determine if the agent's response is GOOD ENOUGH for the customer, not perfect.

Grade 'yes' if the response:
- Attempts to address the customer's main concern
- Provides some relevant information, even if not complete
- Shows the agent understood the question
- Gives next steps, contact info, or acknowledges limitations
- Is polite and professional

Grade 'no' ONLY if the response:
- Completely ignores the customer's question
- Provides completely irrelevant information
- Is rude or unprofessional
- Contains obvious errors or contradictions
- Provides no value whatsoever to the customer

ACCEPTABLE responses include:
- "I need to check your account details first, can you provide your phone number?"
- "Let me transfer you to our technical team who can help with that"
- "I don't have access to that information, but I can schedule a callback"
- Partial answers that help move the conversation forward

UNACCEPTABLE responses include:
- Talking about pizza when asked about phone bills
- Being rude or dismissive
- Giving completely wrong information
- Ignoring the question entirely

Remember: Call center agents often need to gather information, transfer calls, or provide partial help. Grade based on whether this response moves the conversation in a helpful direction, not whether it's a complete solution."""

answer_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "Customer question: {question}\n\nAgent response: {generation}\n\nIs this response good enough for a call center interaction?"),
    ]
)

answer_grader = answer_prompt | structured_llm_grader