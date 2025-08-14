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

structured_llm_grader = llm.with_structured_output(GradeAnswer)

system = """You are a grader assessing whether a call center response adequately addresses the customer's question.

Grade 'yes' if the answer:
- Directly addresses what the customer asked
- Provides actionable information or clear next steps
- Is helpful for resolving the customer's issue

Grade 'no' if the answer:
- Doesn't address the specific question
- Is too vague or generic
- Leaves the customer without clear guidance

Focus on customer satisfaction - would this response help the customer?"""
answer_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "User question: \n\n {question} \n\n LLM generation: {generation}"),
    ]
)

answer_grader = answer_prompt | structured_llm_grader