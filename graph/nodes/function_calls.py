"""
Function calls node for telecom call center.
Handles API calls to retrieve user-specific information.
"""
import hashlib
import requests
import json
import re
from typing import Dict, Any, Optional

from graph.memory import redis_memory, with_memory
from graph.state import GraphState
from langchain.tools import tool
from langchain_groq import ChatGroq
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
    # Turkish phone number patterns
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
            # Normalize to international format
            phone = re.sub(r'\s', '', phone)  # Remove spaces
            if phone.startswith('0'):
                phone = '+90' + phone[1:]
            return phone

    return None

def test_api_connection() -> bool:
    """Test if telecom API is accessible"""
    try:
        response = requests.get(f"{TELECOM_API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"⚠️ API connection test failed: {e}")
        return False

# Define your telecom API tools - REAL API ONLY
@tool
def get_user_package_info(phone_number: str) -> str:
    """Get user's package information using the real API."""
    try:
        print(f"🌐 Calling real API for package info: {phone_number}")

        # Find user first
        users_response = requests.get(f"{TELECOM_API_BASE_URL}/api/v1/users", timeout=API_TIMEOUT)
        if users_response.status_code != 200:
            error_msg = f"Cannot access user database. Status: {users_response.status_code}"
            print(f"❌ {error_msg}")
            return json.dumps({"error": error_msg}, ensure_ascii=False)

        users_data = users_response.json()
        user = None
        for u in users_data.get('users', []):
            if u.get('phone_number') == phone_number:
                user = u
                break

        if not user:
            error_msg = f"User not found with phone number: {phone_number}"
            print(f"❌ {error_msg}")
            return json.dumps({"error": error_msg}, ensure_ascii=False)

        # Get package info
        package_response = requests.get(
            f"{TELECOM_API_BASE_URL}/api/v1/user-info/{user['id']}/package",
            timeout=API_TIMEOUT
        )

        if package_response.status_code == 200:
            result = package_response.json()
            print(f"✅ Package info retrieved successfully")
            return json.dumps(result, ensure_ascii=False, indent=2)
        else:
            error_msg = f"Package info unavailable. Status: {package_response.status_code}"
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
    """Get user's billing information using the real API."""
    try:
        print(f"🌐 Calling real API for bill info: {phone_number}")

        # Find user first
        users_response = requests.get(f"{TELECOM_API_BASE_URL}/api/v1/users", timeout=API_TIMEOUT)
        if users_response.status_code != 200:
            error_msg = f"Cannot access user database. Status: {users_response.status_code}"
            print(f"❌ {error_msg}")
            return json.dumps({"error": error_msg}, ensure_ascii=False)

        users_data = users_response.json()
        user = None
        for u in users_data.get('users', []):
            if u.get('phone_number') == phone_number:
                user = u
                break

        if not user:
            error_msg = f"User not found with phone number: {phone_number}"
            print(f"❌ {error_msg}")
            return json.dumps({"error": error_msg}, ensure_ascii=False)

        # Get bill info
        bills_response = requests.get(
            f"{TELECOM_API_BASE_URL}/api/v1/user-info/{user['id']}/bills",
            timeout=API_TIMEOUT
        )

        if bills_response.status_code == 200:
            result = bills_response.json()
            print(f"✅ Bill info retrieved successfully")
            return json.dumps(result, ensure_ascii=False, indent=2)
        else:
            error_msg = f"Bill info unavailable. Status: {bills_response.status_code}"
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
def get_user_usage_info(phone_number: str) -> str:
    """Get user's current usage information (data, minutes, SMS)."""
    try:
        print(f"🌐 Calling real API for usage info: {phone_number}")

        # Find user first
        users_response = requests.get(f"{TELECOM_API_BASE_URL}/api/v1/users", timeout=API_TIMEOUT)
        if users_response.status_code != 200:
            error_msg = f"Cannot access user database. Status: {users_response.status_code}"
            print(f"❌ {error_msg}")
            return json.dumps({"error": error_msg}, ensure_ascii=False)

        users_data = users_response.json()
        user = None
        for u in users_data.get('users', []):
            if u.get('phone_number') == phone_number:
                user = u
                break

        if not user:
            error_msg = f"User not found with phone number: {phone_number}"
            print(f"❌ {error_msg}")
            return json.dumps({"error": error_msg}, ensure_ascii=False)

        # Get usage info (using package endpoint for now, update if you have a separate usage endpoint)
        usage_response = requests.get(
            f"{TELECOM_API_BASE_URL}/api/v1/user-info/{user['id']}/package",
            timeout=API_TIMEOUT
        )

        if usage_response.status_code == 200:
            result = usage_response.json()
            print(f"✅ Usage info retrieved successfully")
            return json.dumps(result, ensure_ascii=False, indent=2)
        else:
            error_msg = f"Usage info unavailable. Status: {usage_response.status_code}"
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
def get_user_support_tickets(phone_number: str) -> str:
    """Get user's support tickets using the real API."""
    try:
        print(f"🌐 Calling real API for support tickets: {phone_number}")

        # Find user first
        users_response = requests.get(f"{TELECOM_API_BASE_URL}/api/v1/users", timeout=API_TIMEOUT)
        if users_response.status_code != 200:
            error_msg = f"Cannot access user database. Status: {users_response.status_code}"
            print(f"❌ {error_msg}")
            return json.dumps({"error": error_msg}, ensure_ascii=False)

        users_data = users_response.json()
        user = None
        for u in users_data.get('users', []):
            if u.get('phone_number') == phone_number:
                user = u
                break

        if not user:
            error_msg = f"User not found with phone number: {phone_number}"
            print(f"❌ {error_msg}")
            return json.dumps({"error": error_msg}, ensure_ascii=False)

        # Get support tickets
        tickets_response = requests.get(
            f"{TELECOM_API_BASE_URL}/api/v1/user-info/{user['id']}/tickets",
            timeout=API_TIMEOUT
        )

        if tickets_response.status_code == 200:
            result = tickets_response.json()
            print(f"✅ Support tickets retrieved successfully")
            return json.dumps(result, ensure_ascii=False, indent=2)
        else:
            error_msg = f"Support tickets unavailable. Status: {tickets_response.status_code}"
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

# List of all available tools
telecom_tools = [
    get_user_package_info,
    get_user_bill_info,
    get_user_usage_info,
    get_user_support_tickets
]

# LLM with tools bound
llm_with_tools = llm.bind_tools(telecom_tools)

@with_memory
def function_calls_node(state: GraphState) -> GraphState:
    """Execute function calls with Redis memory and caching - REAL API ONLY"""
    print("🔧 Executing function calls with memory (REAL API)...")

    question = state["question"]
    conversation_id = state["conversation_id"]
    user_context = state.get("user_context", {})
    conversation_history = state.get("conversation_history", [])

    try:
        # Try to get phone number from multiple sources with memory
        phone_number = extract_phone_number(question)

        # Check user context from memory
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
            for msg in reversed(conversation_history):
                if msg["role"] == "user":
                    historical_phone = extract_phone_number(msg["content"])
                    if historical_phone:
                        phone_number = historical_phone
                        print(f"📱 Found phone number in conversation history: {phone_number}")
                        break

        if phone_number:
            # Link conversation to phone for future reference
            redis_memory.link_conversation_to_phone(conversation_id, phone_number)

            # Create cache key for API response
            cache_key = hashlib.md5(f"{phone_number}:{question}".encode()).hexdigest()

            # Check cache first
            cached_response = redis_memory.get_cached_api_response(cache_key)
            if cached_response:
                print("💾 Using cached API response")
                return {
                    **state,
                    "tool_results": cached_response,
                    "user_context": {**user_context, "phone_number": phone_number}
                }

            # Check if API is available before making calls
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

            # Determine which tool to use based on question content
            question_lower = question.lower()
            tool_results = {}

            if any(word in question_lower for word in ["paket", "tarife", "plan", "package"]):
                print(f"🛠️ Using tool: get_user_package_info")
                result = get_user_package_info.invoke({"phone_number": phone_number})
                tool_results = {"get_user_package_info": result}

            elif any(word in question_lower for word in ["kullanım", "kalan", "gb", "dakika", "usage"]):
                print(f"🛠️ Using tool: get_user_usage_info")
                result = get_user_usage_info.invoke({"phone_number": phone_number})
                tool_results = {"get_user_usage_info": result}

            elif any(word in question_lower for word in ["fatura", "ödeme", "borç", "bill"]):
                print(f"🛠️ Using tool: get_user_bill_info")
                result = get_user_bill_info.invoke({"phone_number": phone_number})
                tool_results = {"get_user_bill_info": result}

            elif any(word in question_lower for word in ["destek", "ticket", "sorun", "şikayet"]):
                print(f"🛠️ Using tool: get_user_support_tickets")
                result = get_user_support_tickets.invoke({"phone_number": phone_number})
                tool_results = {"get_user_support_tickets": result}

            else:
                # Default to package info
                print(f"🛠️ Using default tool: get_user_package_info")
                result = get_user_package_info.invoke({"phone_number": phone_number})
                tool_results = {"get_user_package_info": result}

            # Cache the API response (only if successful)
            try:
                # Check if the result indicates success before caching
                for tool_name, tool_result in tool_results.items():
                    result_data = json.loads(tool_result) if isinstance(tool_result, str) else tool_result
                    if "error" not in result_data:
                        redis_memory.cache_api_response(cache_key, tool_results, ttl_minutes=5)
                        print("💾 API response cached")
                        break
            except:
                pass  # Don't cache if there's an error parsing the result

            # Update user context with phone number
            updated_user_context = {**user_context, "phone_number": phone_number}

            print(f"📊 Function calls completed successfully.")

            return {
                **state,
                "tool_results": tool_results,
                "user_context": updated_user_context
            }

        else:
            # Check if we already asked for phone number recently
            recent_requests = [msg for msg in conversation_history[-4:]
                             if "telefon numaranızı belirtiniz" in msg.get("content", "")]

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

        error_result = {
            "error": "function_call_failed",
            "message": f"Sistem hatası: {str(e)}"
        }

        return {
            **state,
            "tool_results": {"error": json.dumps(error_result, ensure_ascii=False)}
        }

# Test functions for real API
def test_real_api():
    """Test real API calls"""
    print("\n=== Real API Test ===")

    if not test_api_connection():
        print("❌ API server not available. Make sure your API is running on", TELECOM_API_BASE_URL)
        return

    test_phone = "+905551234567"  # Use a real phone number from your database

    print(f"Testing with phone number: {test_phone}")

    # Test package info
    print("\n1. Testing Package Info...")
    package_result = get_user_package_info.invoke({"phone_number": test_phone})
    print(f"Result: {package_result[:200]}...")

    # Test bill info
    print("\n2. Testing Bill Info...")
    bill_result = get_user_bill_info.invoke({"phone_number": test_phone})
    print(f"Result: {bill_result[:200]}...")

if __name__ == "__main__":
    # Test phone extraction
    print("=== Phone Number Extraction Test ===")
    test_cases = [
        "0555 123 45 67",
        "+90 555 123 45 67",
        "Benim numaram 0533 987 65 43",
        "Paketim nedir?",
        "+905551234567"
    ]

    for text in test_cases:
        phone = extract_phone_number(text)
        print(f"'{text}' → {phone or 'NOT_FOUND'}")

    # Test real API
    test_real_api()