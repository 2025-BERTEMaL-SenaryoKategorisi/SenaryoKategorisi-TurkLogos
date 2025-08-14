"""
TürkLogos Telecom Customer Support Agent
LangChain tabanlı müşteri hizmetleri ajanı
"""
import os
import json
from typing import Dict, Any, List, Optional, Annotated
from datetime import datetime
from groq import Groq

from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.llms import Ollama
from typing import TypedDict
# LangGraph imports - fallback to simple agent if not available
try:
    from langgraph.graph import StateGraph, END
    from langgraph.graph import add_messages
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.user_service import EnhancedUserService
from app.services.package_service import PackageService
from app.models.user import User
from app.models.package import Package
from app.models.bill import Bill
from app.models.support_ticket import SupportTicket
from app.models.technicisian_visit import TechnicianVisit
from app.core.config import settings
from loguru import logger

# =====================================================
# STATE DEFINITION FOR LANGGRAPH (if available)
# =====================================================

if LANGGRAPH_AVAILABLE:
    class AgentState(TypedDict):
        """Agent durumu - conversation tracking için."""
        messages: Annotated[List[BaseMessage], add_messages]
        user_authenticated: bool
        session_id: Optional[str]
        customer_id: Optional[str]
        conversation_context: Dict[str, Any]
else:
    # Dummy class if LangGraph not available
    class AgentState(TypedDict):
        pass

# =====================================================
# LANGCHAIN TOOLS - LLM Tools'ları LangChain formatına çevirme
# =====================================================

@tool
def authenticate_user_tool(phone_number: str, tc_kimlik: str = None, birth_date: str = None) -> Dict[str, Any]:
    """
    Müşteri kimlik doğrulama aracı. Telefon numarası, TC kimlik ve doğum tarihi ile doğrulama.
    Args:
        phone_number: Müşteri telefon numarası (+90XXXXXXXXXX formatında)
        tc_kimlik: TC kimlik numarası (11 haneli)
        birth_date: Doğum tarihi (YYYY-MM-DD formatında)
    Returns:
        Kimlik doğrulama sonucu ve session bilgileri
    """
    from app.schemas.auth import AuthenticationRequest
    from datetime import date
    
    try:
        # Parse birth_date if provided
        birth_date_obj = None
        if birth_date:
            try:
                birth_date_obj = datetime.strptime(birth_date, "%Y-%m-%d").date()
            except ValueError:
                return {"error": "Geçersiz doğum tarihi formatı. YYYY-MM-DD formatında giriniz."}
        
        auth_request = AuthenticationRequest(
            phone_number=phone_number,
            tc_kimlik=tc_kimlik,
            birth_date=birth_date_obj
        )
        
        # Database session'ı al
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            service = EnhancedUserService(db)
            result = service.authenticate_user(auth_request)
            
            return {
                "authenticated": result.authenticated,
                "session_id": result.session_id,
                "user_id": result.user_id,
                "full_name": result.full_name,
                "requires_tc_kimlik": result.requires_tc_kimlik,
                "requires_birth_date": result.requires_birth_date,
                "error_message": result.error_message
            }
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Authentication tool error: {e}")
        return {"error": f"Kimlik doğrulama sırasında hata: {str(e)}"}

@tool
def get_user_info_tool(session_id: str) -> Dict[str, Any]:
    """
    Doğrulanmış kullanıcının detaylı bilgilerini getir.
    Args:
        session_id: Kimlik doğrulama sonrası alınan session ID
    Returns:
        Kullanıcı bilgileri (ad, paket, bakiye, kullanım vb.)
    """
    try:
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            service = EnhancedUserService(db)
            user_info = service.get_user_info(session_id)
            
            if not user_info:
                return {"error": "Geçersiz veya süresi dolmuş session"}
            
            return user_info.dict()
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"User info tool error: {e}")
        return {"error": f"Kullanıcı bilgileri alınırken hata: {str(e)}"}

@tool
def get_available_packages_tool(session_id: str) -> Dict[str, Any]:
    """
    Kullanıcı için uygun paketleri listele.
    Args:
        session_id: Kimlik doğrulama session ID
    Returns:
        Kişiselleştirilmiş paket önerileri
    """
    try:
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            service = EnhancedUserService(db)
            user_data = service._get_session_data(session_id)
            
            if not user_data:
                return {"error": "Geçersiz veya süresi dolmuş session"}
            
            packages = PackageService.get_available_packages(user_data['user_id'], db)
            
            return {
                "success": True,
                "packages": packages,
                "total_count": len(packages),
                "message": f"Size özel {len(packages)} paket önerisi hazırlandı."
            }
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Packages tool error: {e}")
        return {"error": f"Paketler getirilirken hata: {str(e)}"}

@tool 
def get_current_bill_tool(session_id: str) -> Dict[str, Any]:
    """
    Kullanıcının güncel fatura bilgilerini getir.
    Args:
        session_id: Kimlik doğrulama session ID
    Returns:
        Güncel fatura detayları
    """
    try:
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            service = EnhancedUserService(db)
            user_data = service._get_session_data(session_id)
            
            if not user_data:
                return {"error": "Geçersiz veya süresi dolmuş session"}
            
            # Get current month's bill
            current_date = datetime.now().date()
            bill = db.query(Bill).filter(
                Bill.user_id == user_data['user_id'],
                Bill.billing_period_start <= current_date,
                Bill.billing_period_end >= current_date
            ).first()
            
            if not bill:
                return {"error": "Bu ay için fatura bulunamadı"}
            
            return {
                "bill_id": bill.bill_id,
                "total_amount": bill.total_amount,
                "base_amount": bill.base_amount,
                "usage_charges": bill.usage_charges,
                "taxes": bill.taxes,
                "discounts": bill.discounts,
                "due_date": bill.due_date.isoformat(),
                "payment_status": bill.payment_status,
                "billing_period_start": bill.billing_period_start.isoformat(),
                "billing_period_end": bill.billing_period_end.isoformat(),
                "data_used_gb": bill.data_used_gb,
                "voice_used_minutes": bill.voice_used_minutes,
                "sms_used_count": bill.sms_used_count
            }
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Bill tool error: {e}")
        return {"error": f"Fatura bilgileri alınırken hata: {str(e)}"}

@tool
def change_package_tool(session_id: str, new_package_id: str, effective_date: str = None) -> Dict[str, Any]:
    """
    Kullanıcının paketini değiştir.
    Args:
        session_id: Kimlik doğrulama session ID
        new_package_id: Yeni paket ID'si
        effective_date: Paket değişiklik tarihi (isteğe bağlı)
    Returns:
        Paket değişikliği sonucu
    """
    try:
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            service = EnhancedUserService(db)
            user_data = service._get_session_data(session_id)
            
            if not user_data:
                return {"error": "Geçersiz veya süresi dolmuş session"}
            
            result = PackageService.initiate_package_change(
                customer_id=user_data['user_id'],
                package_code=new_package_id,
                session_id=session_id,
                db=db
            )
            
            return result
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Package change tool error: {e}")
        return {"error": f"Paket değişikliği sırasında hata: {str(e)}"}

@tool
def create_support_ticket_tool(session_id: str, subject: str, description: str, category: str = "general", priority: str = "medium") -> Dict[str, Any]:
    """
    Destek talebi oluştur.
    Args:
        session_id: Kimlik doğrulama session ID
        subject: Talep konusu
        description: Detaylı açıklama
        category: Kategori (technical, billing, general)
        priority: Öncelik (low, medium, high)
    Returns:
        Oluşturulan destek talebi bilgileri
    """
    try:
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            service = EnhancedUserService(db)
            user_data = service._get_session_data(session_id)
            
            if not user_data:
                return {"error": "Geçersiz veya süresi dolmuş session"}
            
            import uuid
            ticket = SupportTicket(
                ticket_id=f"TKT-{uuid.uuid4().hex[:8].upper()}",
                customer_id=user_data['user_id'],
                subject=subject,
                description=description,
                category=category,
                priority=priority,
                status="open"
            )
            
            db.add(ticket)
            db.commit()
            
            return {
                "success": True,
                "ticket_id": ticket.ticket_id,
                "status": ticket.status,
                "created_at": ticket.created_at.isoformat(),
                "message": "Destek talebiniz başarıyla oluşturuldu"
            }
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Support ticket tool error: {e}")
        return {"error": f"Destek talebi oluşturulurken hata: {str(e)}"}

@tool
def schedule_technician_visit_tool(session_id: str, visit_type: str, preferred_date: str, preferred_time: str, notes: str = None) -> Dict[str, Any]:
    """
    Teknisyen ziyareti randevusu al.
    Args:
        session_id: Kimlik doğrulama session ID
        visit_type: Ziyaret türü (installation, repair, maintenance, inspection)
        preferred_date: Tercih edilen tarih (YYYY-MM-DD formatında)
        preferred_time: Tercih edilen saat (HH:MM formatında)
        notes: Ek notlar (isteğe bağlı)
    Returns:
        Randevu oluşturma sonucu
    """
    try:
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            service = EnhancedUserService(db)
            user_data = service._get_session_data(session_id)
            
            if not user_data:
                return {"error": "Geçersiz veya süresi dolmuş session"}
            
            # Parse visit date and time
            try:
                visit_datetime = datetime.strptime(f"{preferred_date} {preferred_time}", "%Y-%m-%d %H:%M")
            except ValueError:
                return {"error": "Geçersiz tarih/saat formatı. Tarih: YYYY-MM-DD, Saat: HH:MM formatında giriniz"}
            
            import uuid
            visit = TechnicianVisit(
                visit_id=f"VIS-{uuid.uuid4().hex[:8].upper()}",
                customer_id=user_data['user_id'],
                visit_type=visit_type,
                scheduled_date=visit_datetime,
                status="scheduled",
                notes=notes or ""
            )
            
            db.add(visit)
            db.commit()
            
            return {
                "success": True,
                "visit_id": visit.visit_id,
                "scheduled_date": visit.scheduled_date.isoformat(),
                "visit_type": visit.visit_type,
                "status": visit.status,
                "message": "Teknisyen ziyareti başarıyla planlandı"
            }
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Technician visit tool error: {e}")
        return {"error": f"Teknisyen randevusu oluşturulurken hata: {str(e)}"}

@tool
def get_usage_summary_tool(session_id: str) -> Dict[str, Any]:
    """
    Kullanıcının mevcut kullanım özetini getir.
    Args:
        session_id: Kimlik doğrulama session ID
    Returns:
        Veri ve ses kullanım özeti
    """
    try:
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            service = EnhancedUserService(db)
            user_data = service._get_session_data(session_id)
            
            if not user_data:
                return {"error": "Geçersiz veya süresi dolmuş session"}
            
            user = db.query(User).filter(User.customer_id == user_data['user_id']).first()
            if not user:
                return {"error": "Kullanıcı bulunamadı"}
            
            # Get current package limits
            package_limits = {"data_limit_gb": 0, "voice_minutes": 0}
            if user.current_package_id:
                package = db.query(Package).filter(Package.package_id == user.current_package_id).first()
                if package:
                    package_limits = {
                        "data_limit_gb": package.data_limit_gb,
                        "voice_minutes": package.voice_minutes
                    }
            
            return {
                "data_usage_gb": user.data_usage_gb,
                "data_limit_gb": package_limits["data_limit_gb"],
                "data_remaining_gb": max(0, package_limits["data_limit_gb"] - user.data_usage_gb) if package_limits["data_limit_gb"] > 0 else -1,
                "voice_usage_minutes": user.voice_usage_minutes,
                "voice_limit_minutes": package_limits["voice_minutes"],
                "voice_remaining_minutes": max(0, package_limits["voice_minutes"] - user.voice_usage_minutes) if package_limits["voice_minutes"] > 0 else -1
            }
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Usage summary tool error: {e}")
        return {"error": f"Kullanım özeti alınırken hata: {str(e)}"}

# =====================================================
# LANGCHAIN AGENT SETUP
# =====================================================

class TelecomCustomerSupportAgent:
    """TürkLogos Telecom Customer Support Agent."""
    
    def _initialize_llm(self):
        """Initialize LLM - GROQ ONLY for fast testing."""
        # GROQ FIRST - no slow fallbacks!
        try:
            from groq import Groq
            
            # Check if API key is available
            groq_api_key = settings.groq_api_key or os.getenv("GROQ_API_KEY")
            if not groq_api_key:
                logger.error("❌ GROQ_API_KEY not found!")
                logger.error("🔑 Get your free API key from: https://console.groq.com/keys")
                logger.error("💡 Set it with: export GROQ_API_KEY='your_key_here'")
                raise ValueError("Groq API key required for fast testing")
            
            # Use langchain_groq with correct parameters (from documentation)
            try:
                from langchain_groq import ChatGroq
                
                # Correct initialization based on LangChain Groq docs
                llm = ChatGroq(
                    api_key=groq_api_key,  # Use 'api_key' not 'groq_api_key'
                    model=settings.groq_model,  # Use 'model' not 'model_name'
                    temperature=0.1
                    # max_tokens is set per invoke call, not in constructor
                )
                
                # Test the connection
                test_response = llm.invoke("Test")
                logger.info(f"🚀 Groq LLM initialized successfully with {settings.groq_model}")
                logger.info(f"⚡ Groq test successful: {str(test_response)[:50]}...")
                
            except ImportError as e:
                logger.error(f"❌ langchain_groq not available: {e}")
                logger.error("💡 Install with: pip install langchain-groq")
                raise ValueError("langchain_groq package required for Groq integration")
            return llm
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Groq LLM: {e}")
            logger.error("💡 For testing, get a free Groq API key from: https://console.groq.com/keys")
            raise
    
    def _initialize_ollama(self):
        """Initialize Ollama LLM."""
        try:
            self.llm = Ollama(
                base_url=settings.ollama_base_url,
                model=settings.ollama_model,
                temperature=0.1
            )
            logger.info(f"✅ Ollama LLM initialized successfully with {settings.ollama_model}")
            
            # Test the LLM connection
            test_response = self.llm.invoke("Test")
            logger.info(f"✅ Ollama test successful: {test_response[:50]}...")
            return self.llm
            
        except Exception as e:
            import traceback
            logger.error(f"❌ Failed to initialize Ollama LLM: {e}")
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            return None
    
    def __init__(self):
        """Initialize the agent with tools and LLM."""
        self.tools = [
            authenticate_user_tool,
            get_user_info_tool,
            get_available_packages_tool,
            get_current_bill_tool,
            change_package_tool,
            create_support_ticket_tool,
            schedule_technician_visit_tool,
            get_usage_summary_tool
        ]
        
        # Initialize LLM (Groq for speed or Ollama for local)
        self.llm = self._initialize_llm()
        
        # Skip complex agents - use simple conversation approach
        self.use_graph = False
        self.graph = None
            
        # Use modern ChatGroq tool calling (more reliable than ReAct)
        self.llm_with_tools = None
        if True:  # Enable modern tool calling
            try:
                # Bind tools directly to ChatGroq LLM for native tool calling
                self.llm_with_tools = self.llm.bind_tools(self.tools)
                
                # System prompt for modern tool calling
                system_prompt = """Sen TürkLogos şirketinin müşteri hizmetleri ajanısın. Türkçe müşteri hizmetleri sağlıyorsun.

GÖREVLER:
1. Müşterilerin kimlik doğrulamasını yap (telefon + TC kimlik + doğum tarihi)
2. Fatura sorgulamaları yanıtla
3. Paket değişikliği önerilerinde bulun
4. Kullanım bilgilerini sorgula
5. Teknik destek talepleri oluştur
6. Genel telecom sorularını yanıtla

ÖNEMLI KURALLAR:
- Her zaman kibarlık ve profesyonellik içinde ol
- Müşteri bilgilerini doğrulamadan hassas işlemler yapma
- Türkçe yanıtla ve Türk müşteri hizmetleri standartlarını kullan
- Gerektiğinde araçları kullan (tool calling)
- Hata durumlarında açık ve yardımcı ol

Müşteriye hoş geldin mesajı ile başla ve nasıl yardımcı olabileceğini sor."""

                # Create system message with tools information
                from langchain_core.messages import SystemMessage
                
                self.system_message = SystemMessage(content=system_prompt)
                
                logger.info("✅ Modern tool calling agent created successfully!")
                logger.info(f"🔧 Available tools: {[tool.name for tool in self.tools]}")
            except Exception as e:
                logger.error(f"❌ Failed to create modern tool calling agent: {e}")
                self.llm_with_tools = None
        
    def _create_agent_graph(self):
        """Create the agent state graph (only if LangGraph available)."""
        if not LANGGRAPH_AVAILABLE:
            return None
            
        # System prompt
        system_prompt = """Sen TürkLogos şirketinin müşteri hizmetleri ajanısın. Türkçe müşteri hizmetleri sağlıyorsun.

GÖREVLER:
1. Müşterilerin kimlik doğrulamasını yap (telefon + TC kimlik + doğum tarihi)
2. Fatura sorgulamaları yanıtla
3. Paket değişikliği önerilerinde bulun  
4. Kullanım bilgilerini sorgula
5. Teknik destek talepleri oluştur
6. Genel telecom sorularını yanıtla

ÖNEMLI KURALLAR:
- Her zaman kibarlık ve profesyonellik içinde ol
- Müşteri bilgilerini doğrulamadan hassas işlemler yapma
- Türkçe yanıtla ve Türk müşteri hizmetleri standartlarını kullan
- Eğer bir araç kullanmak gerekiyorsa, önce açıkla sonra kullan
- Hata durumlarında açık ve yardımcı ol

ARAÇLAR: Kimlik doğrulama, fatura sorgulama, paket listesi, paket değişikliği, destek talebi oluşturma, kullanım sorguları

Müşteriye hoş geldin mesajı ile başla ve nasıl yardımcı olabileceğini sor."""

        # Use a simpler approach - let create_react_agent handle the prompt
        from langchain_core.prompts import PromptTemplate
        
        # Create a basic ReAct prompt template
        react_template = """Sen TürkLogos AI Müşteri Hizmetleri asistanısın.

Mevcut araçların:
{tools}

Araç isimleri: {tool_names}

Her zaman şu formatı kullan:

Question: gelen soru
Thought: ne düşünüyorsun 
Action: kullanacağın araç adı
Action Input: araç için parametre
Observation: aracın sonucu
... (gerektiği kadar Thought/Action/Action Input/Observation tekrarla)
Thought: son düşünce
Final Answer: müşteriye final cevap

Başla!

Question: {input}
Thought:{agent_scratchpad}"""

        prompt = PromptTemplate.from_template(react_template)
        
        # Create ReAct agent
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt,
        )
        
        # Create agent executor
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=5,
            handle_parsing_errors=True
        )
        
        # Create StateGraph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", self._tools_node)
        
        # Set entry point
        workflow.set_entry_point("agent")
        
        # Add edges
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "tools",
                "end": END
            }
        )
        workflow.add_edge("tools", "agent")
        
        return workflow.compile()
    
    def _agent_node(self, state: AgentState) -> AgentState:
        """Agent reasoning node."""
        messages = state["messages"]
        response = self.agent_executor.invoke({"input": messages})
        
        # Extract the agent's response
        agent_message = AIMessage(content=response["output"])
        
        return {
            "messages": [agent_message],
            "user_authenticated": state.get("user_authenticated", False),
            "session_id": state.get("session_id"),
            "customer_id": state.get("customer_id"),
            "conversation_context": state.get("conversation_context", {})
        }
    
    def _tools_node(self, state: AgentState) -> AgentState:
        """Tools execution node."""
        # This is handled by the agent executor
        return state
    
    def _should_continue(self, state: AgentState) -> str:
        """Decide whether to continue or end."""
        messages = state["messages"]
        last_message = messages[-1]
        
        # If the last message is from the AI and doesn't need tools, end
        if isinstance(last_message, AIMessage):
            return "end"
        
        return "continue"
    
    def process_message(self, message: str, session_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a user message and return agent response."""
        try:
            # Check if we have a working LLM
            if self.llm is None:
                return {
                    "response": "Merhaba! Ben TürkLogos AI Müşteri Hizmetleri asistanınızım. Şu anda AI motor kurulumu tamamlanıyor. Size nasıl yardımcı olabilirim? (Demo modunda çalışıyorum - Ollama bağlantısı kuruluyor)",
                    "session_context": session_context or {},
                    "status": "demo_mode"
                }
            
            if self.use_graph and LANGGRAPH_AVAILABLE:
                # Use StateGraph approach
                initial_state = {
                    "messages": [HumanMessage(content=message)],
                    "user_authenticated": session_context.get("user_authenticated", False) if session_context else False,
                    "session_id": session_context.get("session_id") if session_context else None,
                    "customer_id": session_context.get("customer_id") if session_context else None,
                    "conversation_context": session_context.get("conversation_context", {}) if session_context else {}
                }
                
                # Run the graph
                result = self.graph.invoke(initial_state)
                
                # Extract response
                last_message = result["messages"][-1]
                response_text = last_message.content if hasattr(last_message, 'content') else str(last_message)
                
                return {
                    "response": response_text,
                    "session_context": {
                        "user_authenticated": result.get("user_authenticated", False),
                        "session_id": result.get("session_id"),
                        "customer_id": result.get("customer_id"),
                        "conversation_context": result.get("conversation_context", {})
                    },
                    "status": "success"
                }
            elif self.llm_with_tools is not None:
                # Use modern ChatGroq tool calling
                logger.info(f"🔧 Using modern tool calling for message: {message[:50]}...")
                
                try:
                    from langchain_core.messages import HumanMessage
                    
                    messages = [
                        self.system_message,
                        HumanMessage(content=message)
                    ]
                    
                    logger.info("📞 Calling ChatGroq LLM...")
                    # Call LLM with tools
                    response = self.llm_with_tools.invoke(messages)
                    logger.info("✅ ChatGroq response received")
                
                    # Check if tools were called
                    if response.tool_calls:
                        logger.info(f"🛠️ Tools called: {[tc['name'] for tc in response.tool_calls]}")
                        
                        # Execute tools and get results
                        from langchain_core.messages import ToolMessage
                        
                        for tool_call in response.tool_calls:
                            # Find and execute the tool
                            tool_name = tool_call['name']
                            tool_args = tool_call['args']
                            
                            # Find the tool by name
                            tool_to_execute = next((t for t in self.tools if t.name == tool_name), None)
                            if tool_to_execute:
                                try:
                                    logger.info(f"🔧 Executing tool: {tool_name}")
                                    tool_result = tool_to_execute.invoke(tool_args)
                                    messages.append(ToolMessage(
                                        content=str(tool_result),
                                        tool_call_id=tool_call['id']
                                    ))
                                    logger.info(f"✅ Tool {tool_name} executed successfully")
                                except Exception as e:
                                    logger.error(f"❌ Tool execution error: {e}")
                                    messages.append(ToolMessage(
                                        content=f"Tool error: {str(e)}",
                                        tool_call_id=tool_call['id']
                                    ))
                        
                        # Get final response after tool execution
                        logger.info("📞 Getting final response from ChatGroq...")
                        final_response = self.llm_with_tools.invoke(messages)
                        response_text = final_response.content
                        logger.info("✅ Final response received from ChatGroq")
                    else:
                        logger.info("ℹ️ No tools called, using direct response")
                        response_text = response.content
                    
                    logger.info(f"💬 Agent response: {response_text[:100]}...")
                    
                    return {
                        "response": response_text,
                        "session_context": session_context or {},
                        "status": "success_with_tools"
                    }
                    
                except Exception as e:
                    logger.error(f"❌ Modern tool calling error: {e}")
                    import traceback
                    logger.error(f"❌ Full traceback: {traceback.format_exc()}")
                    
                    # Fallback to simple response
                    simple_response = "Merhaba! TürkLogos müşteri hizmetleri asistanıyım. Size nasıl yardımcı olabilirim?"
                    return {
                        "response": simple_response,
                        "session_context": session_context or {},
                        "status": "error_fallback"
                    }
            else:
                # Fallback: Use direct Ollama conversation without tools
                logger.info(f"💬 Using simple conversation for message: {message[:50]}...")
                
                # Check if user is asking for package change or identity verification
                is_authenticated = session_context and session_context.get("user_authenticated", False)
                has_tc_info = "TC:" in message or "tc:" in message or any(char.isdigit() for char in message if len([c for c in message if c.isdigit()]) >= 10)
                
                if not is_authenticated and (has_tc_info or "doğum" in message.lower() or "telefon" in message.lower()):
                    # User provided identity info - acknowledge and ask what they need
                    conversation_prompt = f"""Sen TürkLogos AI Müşteri Hizmetleri asistanısın.

Müşteri kimlik bilgilerini paylaştı. Şimdi ne için yardıma ihtiyacı olduğunu öğren.

YANITLARIN:
- Kimlik bilgilerini aldığını belirt
- Nasıl yardımcı olabileceğini sor
- 2-3 cümle ile kısa tut
- Tekrarlama yapma

Müşteri mesajı: {message}

Örnek yanıt: "Merhaba! Size yardımcı olmak için buradayım. Kimlik bilgilerinizi onaylayabilirim. Bu bilgilerle size nasıl yardımcı olabilirim?"

Yanıtın:"""
                else:
                    # Normal conversation
                    conversation_prompt = f"""Sen TürkLogos AI Müşteri Hizmetleri asistanısın.

GÖREV: Müşteri hizmetleri sağla, tekrarlama yapma.

YANITLARIN:
- Samimi ve profesyonel 
- Türkçe konuş
- Kısa ve net (maksimum 2-3 cümle)
- TEKRARLAMa YAPMA

ÖNCEKİ MESAJ BAĞLAMI: {session_context.get('last_message', 'Yok') if session_context else 'Yok'}

HİZMETLER:
- Paket değişikliği, fatura bilgileri, kullanım sorguları
- Kimlik doğrulama için: telefon + TC kimlik + doğum tarihi

Müşteri mesajı: {message}

Yanıtın:"""

                # Generate response using Ollama
                response = self.llm.invoke(conversation_prompt)
                
                # Update session context to avoid repetition
                updated_context = session_context.copy() if session_context else {}
                updated_context['last_message'] = message[:100]
                updated_context['last_response'] = response[:100]
                
                return {
                    "response": response.strip(),
                    "session_context": updated_context,
                    "status": "success"
                }
            
        except Exception as e:
            logger.error(f"Agent processing error: {e}")
            return {
                "response": "Üzgünüm, şu anda bir teknik sorun yaşanıyor. Lütfen daha sonra tekrar deneyiniz veya müşteri hizmetleri ile iletişime geçiniz.",
                "session_context": session_context or {},
                "status": "error",
                "error": str(e)
            }

# =====================================================
# GLOBAL AGENT INSTANCE
# =====================================================

# Global agent instance
_agent_instance = None

def get_agent() -> TelecomCustomerSupportAgent:
    """Get or create the global agent instance."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = TelecomCustomerSupportAgent()
    return _agent_instance
