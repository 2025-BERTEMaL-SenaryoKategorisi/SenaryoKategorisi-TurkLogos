"""
Fixed dynamic function calls node - maintains memory while adding dynamic tool selection
"""
import hashlib
import requests
import json
import re
from typing import Dict, Any, Optional, List

from graph.memory import redis_memory, with_memory
from graph.state import GraphState
from langchain.tools import tool
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os

load_dotenv()

# Configuration
TELECOM_API_BASE_URL = os.getenv("TELECOM_API_BASE_URL", "http://localhost:3000")
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "10"))

# Initialize LLM for function calling
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0
)

def extract_phone_number(text: str) -> Optional[str]:
    """Extract Turkish phone number from text"""
    patterns = [
        r'\+90\s?5\d{2}\s?\d{3}\s?\d{2}\s?\d{2}',  # +90 5XX XXX XX XX
        r'05\d{2}\s?\d{3}\s?\d{2}\s?\d{2}',        # 05XX XXX XX XX
        r'\+905\d{8}',                              # +905XXXXXXXX
        r'05\d{8}'                                  # 05XXXXXXXX
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            phone = match.group(0)
            phone = re.sub(r'\s', '', phone)  # Remove spaces
            if phone.startswith('0'):
                phone = '+90' + phone[1:]
            return phone
    return None

def extract_customer_id(text: str) -> Optional[str]:
    """Extract customer ID from text (format: MSTR001, MSTR002, etc.)"""
    pattern = r'MSTR\d{3,}'
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(0).upper() if match else None

def find_user_by_identifier(identifier: str) -> Optional[Dict]:
    """Find user by phone number or customer ID"""
    try:
        response = requests.get(f"{TELECOM_API_BASE_URL}/api/v1/users", timeout=API_TIMEOUT)
        if response.status_code != 200:
            return None

        users_data = response.json()
        for user in users_data.get('users', []):
            if (user.get('phone_number') == identifier or
                user.get('customer_id') == identifier):
                return user
        return None
    except Exception:
        return None

def test_api_connection() -> bool:
    """Test if telecom API is accessible"""
    try:
        response = requests.get(f"{TELECOM_API_BASE_URL}/api/v1/users?limit=1", timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"⚠️ API connection test failed: {e}")
        return False

# ===== WORKING TOOLS (Keep your original working logic) =====

@tool
def get_user_package_info(phone_number: str) -> str:
    """Get user's current package information, data/voice usage, remaining quotas, and package features."""
    try:
        print(f"🌐 Getting package info for: {phone_number}")
        user = find_user_by_identifier(phone_number)
        if not user:
            return json.dumps({"error": f"User not found with phone number: {phone_number}"}, ensure_ascii=False)

        response = requests.get(
            f"{TELECOM_API_BASE_URL}/api/v1/user-info/{user['id']}/package",
            timeout=API_TIMEOUT
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Package info retrieved successfully")
            return json.dumps(result, ensure_ascii=False, indent=2)
        else:
            error_msg = f"Package info unavailable. Status: {response.status_code}"
            print(f"❌ {error_msg}")
            return json.dumps({"error": error_msg}, ensure_ascii=False)
    except requests.exceptions.Timeout:
        error_msg = "API request timed out"
        print(f"❌ {error_msg}")
        return json.dumps({"error": error_msg}, ensure_ascii=False)
    except requests.exceptions.ConnectionError:
        error_msg = "Cannot connect to API server"
        print(f"❌ {error_msg}")
        return json.dumps({"error": error_msg}, ensure_ascii=False)
    except Exception as e:
        error_msg = f"API call failed: {str(e)}"
        print(f"❌ {error_msg}")
        return json.dumps({"error": error_msg}, ensure_ascii=False)

@tool
def get_user_bill_info(phone_number: str) -> str:
    """Get user's billing information, payment history, outstanding balances, and payment status."""
    try:
        print(f"🌐 Getting bill info for: {phone_number}")
        user = find_user_by_identifier(phone_number)
        if not user:
            return json.dumps({"error": f"User not found with phone number: {phone_number}"}, ensure_ascii=False)

        response = requests.get(
            f"{TELECOM_API_BASE_URL}/api/v1/user-info/{user['id']}/bills",
            timeout=API_TIMEOUT
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Bill info retrieved successfully")
            return json.dumps(result, ensure_ascii=False, indent=2)
        else:
            error_msg = f"Bill info unavailable. Status: {response.status_code}"
            print(f"❌ {error_msg}")
            return json.dumps({"error": error_msg}, ensure_ascii=False)
    except Exception as e:
        error_msg = f"API call failed: {str(e)}"
        print(f"❌ {error_msg}")
        return json.dumps({"error": error_msg}, ensure_ascii=False)

@tool
def get_user_support_tickets(phone_number: str) -> str:
    """Get user's support tickets, issue history, current problems, and resolution status."""
    try:
        print(f"🌐 Getting support tickets for: {phone_number}")
        user = find_user_by_identifier(phone_number)
        if not user:
            return json.dumps({"error": f"User not found with phone number: {phone_number}"}, ensure_ascii=False)

        response = requests.get(
            f"{TELECOM_API_BASE_URL}/api/v1/user-info/{user['id']}/tickets",
            timeout=API_TIMEOUT
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Support tickets retrieved successfully")
            return json.dumps(result, ensure_ascii=False, indent=2)
        else:
            error_msg = f"Support tickets unavailable. Status: {response.status_code}"
            print(f"❌ {error_msg}")
            return json.dumps({"error": error_msg}, ensure_ascii=False)
    except Exception as e:
        error_msg = f"API call failed: {str(e)}"
        print(f"❌ {error_msg}")
        return json.dumps({"error": error_msg}, ensure_ascii=False)

@tool
def get_all_packages() -> str:
    """Get all available packages and plans that customers can choose from, including prices and features."""
    try:
        print("🌐 Getting all available packages")
        response = requests.get(f"{TELECOM_API_BASE_URL}/api/v1/packages", timeout=API_TIMEOUT)

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Packages retrieved successfully")
            return json.dumps(result, ensure_ascii=False, indent=2)
        else:
            error_msg = f"Packages unavailable. Status: {response.status_code}"
            print(f"❌ {error_msg}")
            return json.dumps({"error": error_msg}, ensure_ascii=False)
    except Exception as e:
        error_msg = f"API call failed: {str(e)}"
        print(f"❌ {error_msg}")
        return json.dumps({"error": error_msg}, ensure_ascii=False)

@tool
def create_support_ticket(phone_number: str, title: str, description: str, issue_type: str = "teknik", priority: str = "orta") -> str:
    """Create a new support ticket for customer issues.

    Args:
        phone_number: User's phone number
        title: Ticket title
        description: Detailed description of the issue
        issue_type: Type of issue (baglanti, faturalama, hesap, teknik, paket)
        priority: Priority level (dusuk, orta, yuksek)
    """
    try:
        print(f"🌐 Creating support ticket for: {phone_number}")
        user = find_user_by_identifier(phone_number)
        if not user:
            return json.dumps({"error": f"User not found with phone number: {phone_number}"}, ensure_ascii=False)

        import uuid
        ticket_id = f"DLK{str(uuid.uuid4())[:6].upper()}"

        ticket_data = {
            "ticket_id": ticket_id,
            "user_id": user['id'],
            "issue_type": issue_type,
            "priority": priority,
            "title": title,
            "description": description
        }

        response = requests.post(
            f"{TELECOM_API_BASE_URL}/api/v1/tickets",
            json=ticket_data,
            timeout=API_TIMEOUT
        )

        if response.status_code in [200, 201]:
            result = response.json()
            print(f"✅ Support ticket created successfully")
            return json.dumps({
                "success": True,
                "message": f"Support ticket created successfully with ID: {ticket_id}",
                "ticket": result
            }, ensure_ascii=False, indent=2)
        else:
            error_msg = f"Failed to create ticket. Status: {response.status_code}"
            print(f"❌ {error_msg}")
            return json.dumps({"error": error_msg}, ensure_ascii=False)
    except Exception as e:
        error_msg = f"API call failed: {str(e)}"
        print(f"❌ {error_msg}")
        return json.dumps({"error": error_msg}, ensure_ascii=False)

@tool
def change_user_package(phone_number: str, new_package_id: str) -> str:
    """Change user's package to a new one.

    Args:
        phone_number: User's phone number
        new_package_id: New package ID (e.g., 'PKG001', 'PKG002', etc.)
    """
    try:
        print(f"🔄 Changing package for {phone_number} to {new_package_id}")
        user = find_user_by_identifier(phone_number)
        if not user:
            return json.dumps({"error": f"User not found with phone number: {phone_number}"}, ensure_ascii=False)

        # First, verify the new package exists
        packages_response = requests.get(f"{TELECOM_API_BASE_URL}/api/v1/packages", timeout=API_TIMEOUT)
        if packages_response.status_code != 200:
            return json.dumps({"error": "Cannot verify package availability"}, ensure_ascii=False)

        packages = packages_response.json()
        package_exists = any(pkg.get('package_id') == new_package_id for pkg in packages)

        if not package_exists:
            return json.dumps({
                "error": f"Package {new_package_id} not found",
                "available_packages": [pkg.get('package_id') for pkg in packages]
            }, ensure_ascii=False)

        # Update user's package
        update_data = {
            "current_package_id": new_package_id
        }

        response = requests.put(
            f"{TELECOM_API_BASE_URL}/api/v1/users/{user['id']}",
            json=update_data,
            timeout=API_TIMEOUT
        )

        if response.status_code == 200:
            result = response.json()

            # Get the new package details for confirmation
            new_package = next((pkg for pkg in packages if pkg.get('package_id') == new_package_id), None)

            print(f"✅ Package changed successfully")
            return json.dumps({
                "success": True,
                "message": f"Package successfully changed to {new_package_id}",
                "old_package_id": user.get('current_package_id'),
                "new_package_id": new_package_id,
                "new_package_details": {
                    "name": new_package.get('name', 'Unknown') if new_package else 'Unknown',
                    "price": new_package.get('price', 0) if new_package else 0,
                    "data_limit_gb": new_package.get('data_limit_gb', 0) if new_package else 0,
                    "voice_minutes": new_package.get('voice_minutes', 0) if new_package else 0
                },
                "updated_user": result
            }, ensure_ascii=False, indent=2)
        else:
            error_msg = f"Failed to change package. Status: {response.status_code}"
            print(f"❌ {error_msg}")
            return json.dumps({"error": error_msg}, ensure_ascii=False)

    except Exception as e:
        error_msg = f"API call failed: {str(e)}"
        print(f"❌ {error_msg}")
        return json.dumps({"error": error_msg}, ensure_ascii=False)

@tool
def update_user_info(phone_number: str, email: str = None, address: str = None, city: str = None, first_name: str = None, last_name: str = None) -> str:
    """Update user's personal information like email, address, city, or name.

    Args:
        phone_number: User's phone number
        email: New email address (optional)
        address: New address (optional)
        city: New city (optional)
        first_name: New first name (optional)
        last_name: New last name (optional)
    """
    try:
        print(f"📝 Updating user info for: {phone_number}")
        user = find_user_by_identifier(phone_number)
        if not user:
            return json.dumps({"error": f"User not found with phone number: {phone_number}"}, ensure_ascii=False)

        # Prepare update data (only include fields that are provided)
        update_data = {}
        if email is not None:
            update_data["email"] = email
        if address is not None:
            update_data["address"] = address
        if city is not None:
            update_data["city"] = city
        if first_name is not None:
            update_data["first_name"] = first_name
        if last_name is not None:
            update_data["last_name"] = last_name

        if not update_data:
            return json.dumps({"error": "No update fields provided"}, ensure_ascii=False)

        response = requests.put(
            f"{TELECOM_API_BASE_URL}/api/v1/users/{user['id']}",
            json=update_data,
            timeout=API_TIMEOUT
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ User info updated successfully")
            return json.dumps({
                "success": True,
                "message": "User information updated successfully",
                "updated_fields": update_data,
                "updated_user": result
            }, ensure_ascii=False, indent=2)
        else:
            error_msg = f"Failed to update user info. Status: {response.status_code}"
            print(f"❌ {error_msg}")
            return json.dumps({"error": error_msg}, ensure_ascii=False)

    except Exception as e:
        error_msg = f"API call failed: {str(e)}"
        print(f"❌ {error_msg}")
        return json.dumps({"error": error_msg}, ensure_ascii=False)

# List of available tools
telecom_tools = [
    get_user_package_info,
    get_user_bill_info,
    get_user_support_tickets,
    get_all_packages,
    create_support_ticket,
    change_user_package,
    update_user_info
]

# Create a simple mapping for tool execution
TOOL_MAPPING = {
    "get_user_package_info": get_user_package_info,
    "get_user_bill_info": get_user_bill_info,
    "get_user_support_tickets": get_user_support_tickets,
    "get_all_packages": get_all_packages,
    "create_support_ticket": create_support_ticket,
    "change_user_package": change_user_package,
    "update_user_info": update_user_info
}

# LLM with tools bound
llm_with_tools = llm.bind_tools(telecom_tools)

# Simple tool calling prompt
tool_calling_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a telecom call center agent. Based on the customer's question, decide which tools to use.

IMPORTANT: The customer's phone number is: {phone_number}

Available tools:
- get_user_package_info: For package details, usage, remaining data/minutes (needs phone number)
- get_user_bill_info: For billing, payments, outstanding amounts (needs phone number)
- get_user_support_tickets: For existing issues and ticket history (needs phone number)
- get_all_packages: For available packages and pricing (doesn't need phone number)
- create_support_ticket: To create new support tickets (needs phone number, title, description)
- change_user_package: To change user's package (needs phone number, new_package_id)
- update_user_info: To update customer information like email, address, etc. (needs phone number)

If the customer asks about their personal information, ALWAYS use their phone number: {phone_number}

Examples:
- "What's my package?" → use get_user_package_info with phone_number: {phone_number}
- "Show my bills" → use get_user_bill_info with phone_number: {phone_number}
- "What packages are available?" → use get_all_packages (no phone needed)
- "Change my package to PKG002" → use change_user_package with phone_number: {phone_number} and new_package_id: "PKG002"
- "I want to switch to Temel Paket" → use get_all_packages first to find package ID, then change_user_package
- "Update my email to new@email.com" → use update_user_info with phone_number: {phone_number} and email: "new@email.com"
- "Create a complaint about slow internet" → use create_support_ticket with phone_number: {phone_number}

For package changes:
- If customer mentions package by name (like "Temel Paket"), you may need to use get_all_packages first to find the package_id
- Always use the package_id (like PKG001, PKG002) for change_user_package tool"""),
    ("human", "Customer question: {question}")
])

@with_memory
def function_calls_node(state: GraphState) -> GraphState:
    """Fixed dynamic function calls - maintains memory and working logic"""
    print("🔧 Fixed dynamic function calls with memory...")

    question = state["question"]
    conversation_id = state["conversation_id"]
    user_context = state.get("user_context", {})
    conversation_history = state.get("conversation_history", [])

    try:
        # ENHANCED PHONE NUMBER EXTRACTION WITH MEMORY
        phone_number = extract_phone_number(question)
        customer_id = extract_customer_id(question)

        # Check user context from memory FIRST
        if not phone_number and "phone_number" in user_context:
            phone_number = user_context["phone_number"]
            print(f"📱 Using cached phone number from memory: {phone_number}")

        # Check conversation mapping from Redis
        if not phone_number:
            phone_number = redis_memory.get_phone_from_conversation(conversation_id)
            if phone_number:
                print(f"📱 Retrieved phone from conversation mapping: {phone_number}")

        # Check conversation history for phone numbers
        if not phone_number:
            for msg in reversed(conversation_history[-5:]):  # Check last 5 messages
                if msg.get("role") == "user":
                    historical_phone = extract_phone_number(msg.get("content", ""))
                    if historical_phone:
                        phone_number = historical_phone
                        print(f"📱 Found phone number in conversation history: {phone_number}")
                        break

        # Use customer ID if no phone number
        user_identifier = phone_number or customer_id

        if user_identifier:
            # Link conversation to phone for future reference
            if phone_number:
                redis_memory.link_conversation_to_phone(conversation_id, phone_number)

            # Create cache key for API response
            cache_key = hashlib.md5(f"{user_identifier}:{question}".encode()).hexdigest()

            # Check cache first
            cached_response = redis_memory.get_cached_api_response(cache_key)
            if cached_response:
                print("💾 Using cached API response")
                return {
                    **state,
                    "tool_results": cached_response,
                    "user_context": {**user_context, "phone_number": user_identifier}
                }

            # Check if API is available
            if not test_api_connection():
                error_message = "API hizmetimiz şu anda kullanılamıyor. Lütfen daha sonra tekrar deneyiniz."
                print("❌ API not available")
                return {
                    **state,
                    "tool_results": {"error": json.dumps({
                        "error": "api_unavailable",
                        "message": error_message
                    }, ensure_ascii=False)},
                    "generation": error_message
                }

            # === DYNAMIC TOOL CALLING WITH FIXED CONTEXT ===
            print(f"🧠 LLM analyzing question with phone number: {user_identifier}")

            try:
                # Give LLM the phone number context explicitly
                response = llm_with_tools.invoke(
                    tool_calling_prompt.format(
                        question=question,
                        phone_number=user_identifier
                    )
                )

                print(f"🤖 LLM response has tool calls: {bool(hasattr(response, 'tool_calls') and response.tool_calls)}")

                tool_results = {}

                # Execute the tools the LLM decided to use
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    for tool_call in response.tool_calls:
                        tool_name = tool_call["name"]
                        tool_args = tool_call["args"]

                        print(f"🛠️ LLM chose tool: {tool_name} with args: {tool_args}")

                        # ENSURE PHONE NUMBER IS ALWAYS PASSED
                        if tool_name in ["get_user_package_info", "get_user_bill_info", "get_user_support_tickets", "create_support_ticket", "change_user_package", "update_user_info"]:
                            if "phone_number" not in tool_args or not tool_args["phone_number"]:
                                tool_args["phone_number"] = user_identifier
                                print(f"📱 Added phone number to tool args: {user_identifier}")

                        try:
                            # Execute using the mapping
                            if tool_name in TOOL_MAPPING:
                                tool_func = TOOL_MAPPING[tool_name]
                                result = tool_func.invoke(tool_args)
                                tool_results[tool_name] = result
                                print(f"✅ {tool_name} executed successfully")
                            else:
                                print(f"❌ Unknown tool: {tool_name}")
                                tool_results[tool_name] = json.dumps({"error": f"Unknown tool: {tool_name}"}, ensure_ascii=False)

                        except Exception as e:
                            print(f"❌ Error executing {tool_name}: {e}")
                            tool_results[tool_name] = json.dumps({"error": str(e)}, ensure_ascii=False)

                # If no tools were called, use fallback logic (your original approach)
                else:
                    print("🤖 LLM didn't call tools, asking LLM again with simpler prompt")

                    # Try a simpler prompt to force tool selection
                    simple_prompt = f"""Based on this customer question: "{question}"
                    
                    Customer phone: {user_identifier}
                    
                    You MUST call one of these tools:
                    - get_user_package_info (for package/usage questions)  
                    - get_user_bill_info (for billing questions)
                    - get_user_support_tickets (for support questions)
                    - get_all_packages (for available packages)
                    - change_user_package (for package changes)
                    - update_user_info (for info updates)
                    - create_support_ticket (for complaints)
                    
                    Call the most appropriate tool."""

                    try:
                        simple_response = llm_with_tools.invoke(simple_prompt)
                        if hasattr(simple_response, 'tool_calls') and simple_response.tool_calls:
                            for tool_call in simple_response.tool_calls:
                                tool_name = tool_call["name"]
                                tool_args = tool_call["args"]

                                # Ensure phone number
                                if tool_name in ["get_user_package_info", "get_user_bill_info", "get_user_support_tickets", "create_support_ticket", "change_user_package", "update_user_info"]:
                                    if "phone_number" not in tool_args:
                                        tool_args["phone_number"] = user_identifier

                                if tool_name in TOOL_MAPPING:
                                    tool_func = TOOL_MAPPING[tool_name]
                                    result = tool_func.invoke(tool_args)
                                    tool_results[tool_name] = result
                                    break
                        else:
                            # Last resort - default to package info
                            print("🤖 LLM still didn't call tools, using default package info")
                            result = get_user_package_info.invoke({"phone_number": user_identifier})
                            tool_results = {"get_user_package_info": result}
                    except Exception as simple_error:
                        print(f"❌ Simple prompt also failed: {simple_error}")
                        # Ultimate fallback
                        result = get_user_package_info.invoke({"phone_number": user_identifier})
                        tool_results = {"get_user_package_info": result}

            except Exception as llm_error:
                print(f"❌ LLM error, trying one more time with forced tool selection: {llm_error}")

                # Try one more time with even more explicit prompting
                try:
                    force_prompt = f"""You are a call center agent. Customer says: "{question}"
                    
                    Customer phone number: {user_identifier}
                    
                    You MUST use exactly ONE tool. Choose the best tool and call it:
                    
                    For package info → get_user_package_info
                    For billing → get_user_bill_info  
                    For support issues → get_user_support_tickets
                    For seeing all packages → get_all_packages
                    For changing package → change_user_package
                    For updating info → update_user_info
                    For new complaints → create_support_ticket
                    
                    Call the tool now."""

                    force_response = llm_with_tools.invoke(force_prompt)

                    if hasattr(force_response, 'tool_calls') and force_response.tool_calls:
                        tool_call = force_response.tool_calls[0]  # Take first one
                        tool_name = tool_call["name"]
                        tool_args = tool_call["args"]

                        # Ensure phone number
                        if tool_name in ["get_user_package_info", "get_user_bill_info", "get_user_support_tickets", "create_support_ticket", "change_user_package", "update_user_info"]:
                            if "phone_number" not in tool_args:
                                tool_args["phone_number"] = user_identifier

                        if tool_name in TOOL_MAPPING:
                            tool_func = TOOL_MAPPING[tool_name]
                            result = tool_func.invoke(tool_args)
                            tool_results = {tool_name: result}
                        else:
                            # Final fallback
                            result = get_user_package_info.invoke({"phone_number": user_identifier})
                            tool_results = {"get_user_package_info": result}
                    else:
                        # Final fallback
                        result = get_user_package_info.invoke({"phone_number": user_identifier})
                        tool_results = {"get_user_package_info": result}

                except Exception as force_error:
                    print(f"❌ All LLM attempts failed: {force_error}")
                    # Ultimate fallback
                    result = get_user_package_info.invoke({"phone_number": user_identifier})
                    tool_results = {"get_user_package_info": result}

            # Cache the API response (only if successful)
            try:
                for tool_name, tool_result in tool_results.items():
                    result_data = json.loads(tool_result) if isinstance(tool_result, str) else tool_result
                    if "error" not in result_data:
                        redis_memory.cache_api_response(cache_key, tool_results, ttl_minutes=5)
                        print("💾 API response cached")
                        break
            except:
                pass  # Don't cache if there's an error

            # Update user context with phone number
            updated_user_context = {**user_context, "phone_number": user_identifier}

            print(f"📊 Function calls completed successfully. Used {len(tool_results)} tools.")

            return {
                **state,
                "tool_results": tool_results,
                "user_context": updated_user_context
            }

        else:
            # Check if we already asked for phone number recently
            recent_requests = [msg for msg in conversation_history[-4:]
                             if msg.get("content") and "telefon numaranızı belirtiniz" in msg.get("content", "")]

            if recent_requests:
                error_message = "Telefon numaranızı hala alamadım. Lütfen açık bir şekilde belirtiniz: '0555 123 45 67'"
            else:
                error_message = "Kişisel bilgilerinize erişebilmem için telefon numaranızı belirtiniz. Örnek: 0555 123 45 67"

            print("❌ No phone number found in question or memory")

            return {
                **state,
                "tool_results": {"error": json.dumps({
                    "error": "phone_number_required",
                    "message": error_message
                }, ensure_ascii=False)},
                "generation": error_message
            }

    except Exception as e:
        print(f"❌ Error in function_calls_node: {e}")

        # Return a proper error response
        error_result = {
            "error": "function_call_failed",
            "message": f"Sistem hatası: {str(e)}"
        }

        return {
            **state,
            "tool_results": {"error": json.dumps(error_result, ensure_ascii=False)}
        }

# Test function
"""def test_memory_and_dynamic():
    Test that memory and dynamic calling work together
    print("\n=== Memory + Dynamic Tool Calling Test ===")

    # Test state with memory
    test_state = {
        "question": "Paketim nedir?",
        "conversation_id": "test_123",
        "user_context": {"phone_number": "+905551234567"},  # Simulate cached phone
        "conversation_history": []
    }

    print("🧪 Testing with cached phone number in context...")
    print(f"Question: {test_state['question']}")
    print(f"Cached phone: {test_state['user_context']['phone_number']}")

if __name__ == "__main__":
    test_memory_and_dynamic()"""