from typing import Literal
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv(verbose=True)

class RouteQuery(BaseModel):
    """Route a user query to the most relevant datasource."""

    datasource: Literal["vectorstore", "function_calls"] = Field(
        ...,
        description="Given a user question choose to route it to function calls or a vectorstore.",
    )

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0
)
structured_llm_router = llm.with_structured_output(RouteQuery)

system = """You are a smart routing assistant for a Turkish telecom call center that directs user questions to the appropriate data source.

ROUTING RULES:

🗂️ Route to VECTORSTORE for:
- General FAQ about telecom services
- Information about available packages/tariffs we offer
- Company policies and procedures
- Service descriptions and features
- General "how-to" questions about our services
- Coverage areas, roaming info, device compatibility
- Pricing information for plans

🔧 Route to FUNCTION CALLS for:
- Personal account information 
- Real-time usage queries (data, minutes, SMS remaining)
- Bill/invoice requests
- Personal subscription details
- Account operations (recharge, plan change, suspend line)
- Personal data queries (phone number, address, payment history)
- Technical support for user's specific line/device

KEY DISTINCTION:
- "Hangi paketleriniz var?" (What packages do you offer?) → VECTORSTORE (general info)
- "Benim paketim nedir?" (What is my package?) → FUNCTION CALLS (personal lookup)
- "Fatura ödeme nasıl yapılır?" (How to pay bills?) → VECTORSTORE (general policy)
- "Faturamı görebilir miyim?" (Can I see my bill?) → FUNCTION CALLS (personal data)
- "Roaming ücretleri nedir?" (What are roaming charges?) → VECTORSTORE (general pricing)
- "Kalan internetim kaç GB?" (How much data do I have left?) → FUNCTION CALLS (personal usage)

PERSONAL PRONOUN DETECTION:
Turkish: "benim", "bana", "bende", "benimki", "kendim", "-im", "-ım", "-üm", "-um" (possessive suffixes)
English: "my", "I", "me", "mine", "myself"

Examples of Turkish telecom patterns:
- "hattım" (my line) → FUNCTION CALLS
- "paketim" (my package) → FUNCTION CALLS  
- "faturam" (my bill) → FUNCTION CALLS
- "kullanımım" (my usage) → FUNCTION CALLS

SIMPLE RULE: If the question contains personal pronouns or asks about user-specific telecom data (usage, bills, account details), choose FUNCTION CALLS. Otherwise, use VECTORSTORE for general company/service information."""


route_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "{question}"),
    ]
)

question_router = route_prompt | structured_llm_router