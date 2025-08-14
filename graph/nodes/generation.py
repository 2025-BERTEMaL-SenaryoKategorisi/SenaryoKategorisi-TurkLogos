from graph.chains.generation_chain import generation_chain
from graph.memory.memory_nodes import with_memory
from graph.state import GraphState
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser

# Create a Turkish-focused generation chain
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.2
)

# Turkish telecom customer service prompt
turkish_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful Turkish telecom customer service agent. You MUST ALWAYS respond in Turkish.

Key Instructions:
- Always respond in Turkish language only
- Use conversation history to provide personalized responses
- Reference user information naturally when available
- Be helpful, professional, and friendly
- Provide clear and actionable information
- If you have user data from API calls, explain it clearly in Turkish

Your role is to help Turkish telecom customers with their questions about packages, bills, usage, and support."""),

    ("human", """Context: {context}

Current Question: {question}

Please provide a helpful response in Turkish based on the context and question above.""")
])

# Override the generation chain with Turkish prompt
generation_chain = turkish_prompt | llm | StrOutputParser()


@with_memory
def generate_answer_node(state: GraphState) -> GraphState:
    """Generate answer with memory - Always responds in Turkish"""
    print("✍️ Generating answer...")

    question = state["question"]
    conversation_history = state.get("conversation_history", [])
    user_context = state.get("user_context", {})

    try:
        # Build context with memory
        context_parts = []

        # Add conversation history
        if conversation_history:
            recent_history = conversation_history[-4:]
            history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_history])
            context_parts.append(f"Conversation History:\n{history_text}")

        # Add user context
        if user_context:
            user_info = []
            if "phone_number" in user_context:
                user_info.append(f"Phone: {user_context['phone_number']}")
            if "name" in user_context:
                user_info.append(f"Name: {user_context['name']}")
            if "package" in user_context:
                user_info.append(f"Package: {user_context['package']}")

            if user_info:
                context_parts.append(f"User Info: {', '.join(user_info)}")

        # Add documents or tool results
        if state.get("relevant_documents"):
            doc_context = "\n".join([doc.page_content for doc in state["relevant_documents"]])
            context_parts.append(f"Knowledge Base:\n{doc_context}")
        elif state.get("tool_results"):
            # Format tool results nicely
            tool_results = state["tool_results"]
            formatted_results = []

            for tool_name, tool_result in tool_results.items():
                if isinstance(tool_result, str):
                    try:
                        import json
                        parsed_result = json.loads(tool_result)
                        if "data" in parsed_result and parsed_result.get("success"):
                            # Extract key information from successful API calls
                            data = parsed_result["data"]
                            formatted_results.append(
                                f"API Response from {tool_name}: {json.dumps(data, ensure_ascii=False, indent=2)}")
                        else:
                            formatted_results.append(f"API Response from {tool_name}: {tool_result}")
                    except:
                        formatted_results.append(f"API Response from {tool_name}: {tool_result}")
                else:
                    formatted_results.append(f"API Response from {tool_name}: {tool_result}")

            if formatted_results:
                context_parts.append(f"API Data:\n" + "\n".join(formatted_results))

        full_context = "\n\n".join(context_parts) if context_parts else "No additional context available."

        # Generate answer using the Turkish-focused chain
        response = generation_chain.invoke({
            "context": full_context,
            "question": question
        })

        # Add assistant message to conversation history
        updated_history = conversation_history + [{"role": "assistant", "content": response}]

        print(f"Generated: {response[:100]}...")

        return {
            **state,
            "generation": response,
            "conversation_history": updated_history
        }

    except Exception as e:
        print(f"❌ Error generating answer: {e}")
        return {**state, "generation": "Üzgünüm, bir hata oluştu. Lütfen tekrar deneyiniz."}


# Export alias for backward compatibility
generate = generate_answer_node