"""
Function calls node for telecom call center.
Handles API calls to retrieve user-specific information.
"""

import requests
import json
import re
from typing import Dict, Any, Optional
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


# Define your telecom API tools
@tool
def get_user_package_info(phone_number: str) -> str:
    """
    Get user's current package/tariff information.

    Args:
        phone_number: User's phone number (e.g., +905551234567)

    Returns:
        JSON string with package information
    """
    try:
        response = requests.get(
            f"{TELECOM_API_BASE_URL}/api/v1/getUserPackage/{phone_number}",
            timeout=API_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            return json.dumps(data, ensure_ascii=False, indent=2)
        else:
            error_data = response.json() if response.content else {}
            return json.dumps({
                "error": f"API returned status {response.status_code}",
                "message": error_data.get("message", "Unknown error")
            }, ensure_ascii=False)

    except requests.exceptions.RequestException as e:
        return json.dumps({
            "error": "Connection failed",
            "message": str(e)
        }, ensure_ascii=False)


@tool
def get_user_usage_info(phone_number: str) -> str:
    """
    Get user's current usage information (data, minutes, SMS).

    Args:
        phone_number: User's phone number (e.g., +905551234567)

    Returns:
        JSON string with usage information
    """
    try:
        response = requests.post(
            f"{TELECOM_API_BASE_URL}/api/v1/getUserUsage",
            json={"phone_number": phone_number},
            headers={"Content-Type": "application/json"},
            timeout=API_TIMEOUT
        )

        if response.status_code == 200:
            data = response.json()
            return json.dumps(data, ensure_ascii=False, indent=2)
        else:
            error_data = response.json() if response.content else {}
            return json.dumps({
                "error": f"API returned status {response.status_code}",
                "message": error_data.get("message", "Unknown error")
            }, ensure_ascii=False)

    except requests.exceptions.RequestException as e:
        return json.dumps({
            "error": "Connection failed",
            "message": str(e)
        }, ensure_ascii=False)


@tool
def get_user_bill_info(phone_number: str) -> str:
    """
    Get user's billing information and payment status.

    Args:
        phone_number: User's phone number (e.g., +905551234567)

    Returns:
        JSON string with billing information
    """
    try:
        response = requests.get(
            f"{TELECOM_API_BASE_URL}/api/getUserBill/{phone_number}",
            timeout=API_TIMEOUT
        )

        if response.status_code == 200:
            data = response.json()
            return json.dumps(data, ensure_ascii=False, indent=2)
        else:
            error_data = response.json() if response.content else {}
            return json.dumps({
                "error": f"API returned status {response.status_code}",
                "message": error_data.get("message", "Unknown error")
            }, ensure_ascii=False)

    except requests.exceptions.RequestException as e:
        return json.dumps({
            "error": "Connection failed",
            "message": str(e)
        }, ensure_ascii=False)


# List of all available tools
telecom_tools = [
    get_user_package_info,
    get_user_usage_info,
    get_user_bill_info
]

# LLM with tools bound
llm_with_tools = llm.bind_tools(telecom_tools)


def extract_phone_number(text: str) -> Optional[str]:
    """Extract Turkish phone number from text"""
    # Turkish phone number patterns
    patterns = [
        r'\+90\s?5\d{2}\s?\d{3}\s?\d{2}\s?\d{2}',  # +90 5XX XXX XX XX
        r'05\d{2}\s?\d{3}\s?\d{2}\s?\d{2}',  # 05XX XXX XX XX
        r'\+905\d{8}',  # +905XXXXXXXX
        r'05\d{8}'  # 05XXXXXXXX
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


def mock_api_response(tool_name: str, phone_number: str) -> str:
    """Generate mock API responses for testing when real API is not available"""
    mock_data = {
        "get_user_package_info": {
            "success": True,
            "data": {
                "package_name": "Gold Paket",
                "monthly_fee": "79.90 TL",
                "data_quota": "20 GB",
                "voice_quota": "Sınırsız",
                "sms_quota": "1000 SMS",
                "validity": "30 gün",
                "phone_number": phone_number
            }
        },
        "get_user_usage_info": {
            "success": True,
            "data": {
                "remaining_data": "12.5 GB",
                "used_data": "7.5 GB",
                "remaining_voice": "Sınırsız",
                "remaining_sms": "750 SMS",
                "usage_period": "15 Ekim - 15 Kasım",
                "phone_number": phone_number
            }
        },
        "get_user_bill_info": {
            "success": True,
            "data": {
                "current_bill": "79.90 TL",
                "due_date": "25 Kasım 2024",
                "payment_status": "Ödenmedi",
                "last_payment": "79.90 TL - 25 Ekim 2024",
                "phone_number": phone_number
            }
        }
    }

    return json.dumps(mock_data.get(tool_name, {"error": "Unknown tool"}), ensure_ascii=False, indent=2)


def test_api_connection() -> bool:
    """Test if telecom API is accessible"""
    try:
        response = requests.get(f"{TELECOM_API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def function_calls_node(state: GraphState) -> GraphState:
    """
    Execute function calls to retrieve user-specific information.

    Args:
        state: Current graph state containing the question

    Returns:
        Updated state with tool results
    """
    print("🔧 Executing function calls...")

    question = state["question"]

    try:
        # Extract phone number from the question
        phone_number = extract_phone_number(question)

        if phone_number:
            print(f"📱 Extracted phone number: {phone_number}")

            # Determine which tool to use based on question content
            question_lower = question.lower()

            if any(word in question_lower for word in ["paket", "tarife", "plan", "package"]):
                tool_name = "get_user_package_info"
                print(f"🛠️ Using tool: {tool_name}")

                # Try real API first, then mock
                if test_api_connection():
                    result = get_user_package_info.invoke({"phone_number": phone_number})
                else:
                    print("⚠️ API not available, using mock data")
                    result = mock_api_response(tool_name, phone_number)

                tool_results = {tool_name: result}

            elif any(word in question_lower for word in ["kullanım", "kalan", "gb", "dakika", "usage"]):
                tool_name = "get_user_usage_info"
                print(f"🛠️ Using tool: {tool_name}")

                if test_api_connection():
                    result = get_user_usage_info.invoke({"phone_number": phone_number})
                else:
                    print("⚠️ API not available, using mock data")
                    result = mock_api_response(tool_name, phone_number)

                tool_results = {tool_name: result}

            elif any(word in question_lower for word in ["fatura", "ödeme", "borç", "bill"]):
                tool_name = "get_user_bill_info"
                print(f"🛠️ Using tool: {tool_name}")

                if test_api_connection():
                    result = get_user_bill_info.invoke({"phone_number": phone_number})
                else:
                    print("⚠️ API not available, using mock data")
                    result = mock_api_response(tool_name, phone_number)

                tool_results = {tool_name: result}

            else:
                # Default to comprehensive user info
                tool_name = "get_user_complete_info"
                print(f"🛠️ Using tool: {tool_name}")

                if test_api_connection():
                    result = get_user_complete_info.invoke({"phone_number": phone_number})
                else:
                    print("⚠️ API not available, using mock data")
                    result = mock_api_response("get_user_package_info", phone_number)

                tool_results = {tool_name: result}

            print(f"📊 Function calls completed.")

            return {
                **state,
                "tool_results": tool_results
            }

        else:
            # No phone number found - ask user for it
            print("❌ No phone number found in question")

            error_result = {
                "error": "phone_number_required",
                "message": "Lütfen telefon numaranızı belirtiniz. Örnek: 0555 123 45 67"
            }

            return {
                **state,
                "tool_results": {"error": json.dumps(error_result, ensure_ascii=False)}
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


# Updated API tools based on your documentation
@tool
def get_user_complete_info(phone_number: str) -> str:
    """
    Get complete user information including package, billing, and support tickets.

    Args:
        phone_number: User's phone number (e.g., +905551234567)

    Returns:
        JSON string with complete user information
    """
    try:
        # First, find user by phone number
        users_response = requests.get(
            f"{TELECOM_API_BASE_URL}/api/v1/users",
            timeout=API_TIMEOUT
        )

        if users_response.status_code != 200:
            return json.dumps({
                "error": "Cannot access user database",
                "message": "Kullanıcı veritabanına erişilemiyor"
            }, ensure_ascii=False)

        users_data = users_response.json()
        user = None

        # Find user by phone number
        for u in users_data.get('users', []):
            if u.get('phone_number') == phone_number:
                user = u
                break

        if not user:
            return json.dumps({
                "error": "User not found",
                "message": f"Bu telefon numarası ile kayıtlı kullanıcı bulunamadı: {phone_number}"
            }, ensure_ascii=False)

        user_id = user['id']

        # Get complete user information
        complete_response = requests.get(
            f"{TELECOM_API_BASE_URL}/api/v1/user-info/{user_id}/complete",
            timeout=API_TIMEOUT
        )

        if complete_response.status_code == 200:
            return json.dumps(complete_response.json(), ensure_ascii=False, indent=2)
        else:
            return json.dumps({
                "error": f"API returned status {complete_response.status_code}",
                "message": "Kullanıcı bilgileri alınamadı"
            }, ensure_ascii=False)

    except requests.exceptions.RequestException as e:
        return json.dumps({
            "error": "Connection failed",
            "message": f"API bağlantı hatası: {str(e)}"
        }, ensure_ascii=False)


# Updated existing tools to use the new API structure
@tool
def get_user_package_info(phone_number: str) -> str:
    """Get user's package information using the new API structure."""
    try:
        # Find user first
        users_response = requests.get(f"{TELECOM_API_BASE_URL}/api/v1/users")
        if users_response.status_code != 200:
            return json.dumps({"error": "Cannot access user database"}, ensure_ascii=False)

        users_data = users_response.json()
        user = None
        for u in users_data.get('users', []):
            if u.get('phone_number') == phone_number:
                user = u
                break

        if not user:
            return json.dumps({"error": "User not found", "phone_number": phone_number}, ensure_ascii=False)

        # Get package info
        package_response = requests.get(f"{TELECOM_API_BASE_URL}/api/v1/user-info/{user['id']}/package")
        if package_response.status_code == 200:
            return json.dumps(package_response.json(), ensure_ascii=False, indent=2)
        else:
            return json.dumps({"error": f"Package info unavailable"}, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": "Connection failed", "message": str(e)}, ensure_ascii=False)


@tool
def get_user_bill_info(phone_number: str) -> str:
    """Get user's billing information using the new API structure."""
    try:
        # Find user first
        users_response = requests.get(f"{TELECOM_API_BASE_URL}/api/v1/users")
        if users_response.status_code != 200:
            return json.dumps({"error": "Cannot access user database"}, ensure_ascii=False)

        users_data = users_response.json()
        user = None
        for u in users_data.get('users', []):
            if u.get('phone_number') == phone_number:
                user = u
                break

        if not user:
            return json.dumps({"error": "User not found", "phone_number": phone_number}, ensure_ascii=False)

        # Get bill info
        bills_response = requests.get(f"{TELECOM_API_BASE_URL}/api/v1/user-info/{user['id']}/bills")
        if bills_response.status_code == 200:
            return json.dumps(bills_response.json(), ensure_ascii=False, indent=2)
        else:
            return json.dumps({"error": f"Bill info unavailable"}, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": "Connection failed", "message": str(e)}, ensure_ascii=False)


@tool
def get_user_support_tickets(phone_number: str) -> str:
    """Get user's support tickets using the new API structure."""
    try:
        # Find user first
        users_response = requests.get(f"{TELECOM_API_BASE_URL}/api/v1/users")
        if users_response.status_code != 200:
            return json.dumps({"error": "Cannot access user database"}, ensure_ascii=False)

        users_data = users_response.json()
        user = None
        for u in users_data.get('users', []):
            if u.get('phone_number') == phone_number:
                user = u
                break

        if not user:
            return json.dumps({"error": "User not found", "phone_number": phone_number}, ensure_ascii=False)

        # Get support tickets
        tickets_response = requests.get(f"{TELECOM_API_BASE_URL}/api/v1/user-info/{user['id']}/tickets")
        if tickets_response.status_code == 200:
            return json.dumps(tickets_response.json(), ensure_ascii=False, indent=2)
        else:
            return json.dumps({"error": f"Support tickets unavailable"}, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": "Connection failed", "message": str(e)}, ensure_ascii=False)


# Updated tools list
telecom_tools = [
    get_user_package_info,
    get_user_bill_info,
    get_user_support_tickets,
    get_user_complete_info
]


# Test functions
def test_function_calls():
    """Test function calls with real API"""
    print("\n=== Function Calls Test ===")

    test_questions = [
        "Benim paketim nedir? 0555 123 45 67",
        "Faturamı görebilir miyim? +90 555 123 45 67",
        "Destek biletlerim var mı? 0533 987 65 43"
    ]

    for question in test_questions:
        print(f"\nQuestion: {question}")
        phone = extract_phone_number(question)
        if phone:
            print(f"Extracted phone: {phone}")
            # Test with real API if available
            if test_api_connection():
                result = get_user_package_info.invoke({"phone_number": phone})
                print(f"API result: {result[:200]}...")
            else:
                print("API not available - would use mock data")
        else:
            print("No phone number found")


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

    # Test function calls
    test_function_calls()

    # Test API connection
    print(f"\n=== API Connection Test ===")
    if test_api_connection():
        print("✅ API is accessible")
    else:
        print("❌ API is not accessible - will use mock data")