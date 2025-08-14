"""
Chat API endpoints for AI agent conversations
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import uuid
import traceback

from app.core.database import get_db
from app.agent.customer_support_agent import get_agent
from app.models.conversation import Conversation
from app.models.user import User
from loguru import logger

router = APIRouter()

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    conversation_context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    conversation_context: Optional[Dict[str, Any]] = None
    status: str = "success"
    error: Optional[str] = None

class ConversationHistory(BaseModel):
    conversation_id: str
    messages: List[Dict[str, Any]]
    created_at: str
    updated_at: str

@router.post("/", response_model=ChatResponse)
async def chat(message: ChatMessage, db: Session = Depends(get_db)):
    """Handle chat messages from users with TürkLogos AI Agent."""
    try:
        logger.info(f"Received chat message: {message.message[:100]}...")
        
        # Generate session ID if not provided
        session_id = message.session_id or str(uuid.uuid4())
        
        # Get agent instance
        agent = get_agent()
        
        # Prepare session context
        session_context = {
            "user_authenticated": False,
            "session_id": None,
            "customer_id": None,
            "conversation_context": message.conversation_context or {}
        }
        
        # If session_id provided, try to get existing context
        if message.session_id:
            session_context.update(message.conversation_context or {})
        
        # Process message with agent
        agent_result = agent.process_message(
            message=message.message,
            session_context=session_context
        )
        
        # Log conversation to database
        try:
            conversation = Conversation(
                conversation_id=session_id,
                user_message=message.message,
                agent_response=agent_result["response"],
                session_context=agent_result.get("session_context", {}),
                user_id=message.user_id
            )
            db.add(conversation)
            db.commit()
            logger.info(f"Conversation logged for session: {session_id}")
        except Exception as e:
            logger.warning(f"Failed to log conversation: {e}")
            # Don't fail the chat if logging fails
        
        return ChatResponse(
            response=agent_result["response"],
            session_id=session_id,
            conversation_context=agent_result.get("session_context"),
            status=agent_result["status"],
            error=agent_result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        logger.error(f"Chat error traceback: {traceback.format_exc()}")
        
        # Return friendly error message
        return ChatResponse(
            response="Üzgünüm, şu anda bir teknik sorun yaşanıyor. Lütfen daha sonra tekrar deneyiniz. Acil durumlar için müşteri hizmetleri: 444 0 TLG",
            session_id=message.session_id or str(uuid.uuid4()),
            conversation_context=message.conversation_context,
            status="error",
            error=str(e)
        )

@router.get("/sessions/{session_id}")
async def get_chat_history(session_id: str, db: Session = Depends(get_db)):
    """Get chat history for a session."""
    try:
        conversations = db.query(Conversation).filter(
            Conversation.conversation_id == session_id
        ).order_by(Conversation.created_at).all()
        
        messages = []
        for conv in conversations:
            messages.extend([
                {
                    "type": "human",
                    "content": conv.user_message,
                    "timestamp": conv.created_at.isoformat()
                },
                {
                    "type": "ai", 
                    "content": conv.agent_response,
                    "timestamp": conv.created_at.isoformat()
                }
            ])
        
        return {
            "session_id": session_id,
            "messages": messages,
            "total_messages": len(messages),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Chat history error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat history retrieval failed: {str(e)}")

@router.get("/sessions/{session_id}/context")
async def get_session_context(session_id: str, db: Session = Depends(get_db)):
    """Get session context for active conversation."""
    try:
        # Get latest conversation for this session
        latest_conv = db.query(Conversation).filter(
            Conversation.conversation_id == session_id
        ).order_by(Conversation.created_at.desc()).first()
        
        if not latest_conv:
            return {
                "session_id": session_id,
                "context": {},
                "status": "no_context"
            }
        
        return {
            "session_id": session_id,
            "context": latest_conv.session_context or {},
            "last_updated": latest_conv.updated_at.isoformat(),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Session context error: {e}")
        raise HTTPException(status_code=500, detail=f"Session context retrieval failed: {str(e)}")

@router.delete("/sessions/{session_id}")
async def clear_session(session_id: str, db: Session = Depends(get_db)):
    """Clear conversation history for a session."""
    try:
        deleted_count = db.query(Conversation).filter(
            Conversation.conversation_id == session_id
        ).delete()
        
        db.commit()
        
        return {
            "session_id": session_id,
            "deleted_messages": deleted_count,
            "status": "success",
            "message": "Conversation history cleared"
        }
        
    except Exception as e:
        logger.error(f"Clear session error: {e}")
        raise HTTPException(status_code=500, detail=f"Session clear failed: {str(e)}")

@router.get("/health")
async def chat_health_check():
    """Check if chat agent is healthy."""
    try:
        agent = get_agent()
        
        # Test agent with simple message
        test_result = agent.process_message("Merhaba", {})
        
        return {
            "status": "healthy",
            "agent_loaded": True,
            "test_response_length": len(test_result.get("response", "")),
            "tools_count": len(agent.tools),
            "message": "Chat agent is ready to serve customers"
        }
        
    except Exception as e:
        logger.error(f"Chat health check failed: {e}")
        return {
            "status": "unhealthy",
            "agent_loaded": False,
            "error": str(e),
            "message": "Chat agent is not ready"
        }
