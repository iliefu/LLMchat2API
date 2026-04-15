from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import json
from uuid import uuid4
from datetime import datetime
from typing import List
import logging

# Import LLM wrappers
try:
    from chatrapper import AsyncRapper
except ImportError:
    AsyncRapper = None

try:
    from qwen_wrapper import AsyncQwenRapper
except ImportError:
    AsyncQwenRapper = None

from conversation_manager import ConversationManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="LLMchat2API",
    description="OpenAI-compatible API for ChatGPT and Qwen web interfaces",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize conversation manager
db = ConversationManager()

# Configuration
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai")  # "openai" or "qwen"
CHATRAPPER_TOKEN = os.environ.get("CHATRAPPER_TOKEN")
QWEN_TOKEN = os.environ.get("QWEN_TOKEN")

# Conversation storage
conversations = {}

class ConversationContext:
    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id
        self.messages: List[dict] = []
    
    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})

# ============ Health & Info Endpoints ============

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "LLMchat2API",
        "provider": LLM_PROVIDER,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/v1/models")
async def list_models():
    """List available models (OpenAI compatible)"""
    if LLM_PROVIDER == "qwen":
        return {
            "object": "list",
            "data": [
                {"id": "qwen-max", "object": "model", "owned_by": "alibaba"},
                {"id": "qwen-plus", "object": "model", "owned_by": "alibaba"},
                {"id": "qwen-turbo", "object": "model", "owned_by": "alibaba"},
            ]
        }
    else:  # openai
        return {
            "object": "list",
            "data": [
                {"id": "text-davinci-002-render-sha", "object": "model", "owned_by": "openai"},
                {"id": "gpt-4", "object": "model", "owned_by": "openai"},
            ]
        }

# ============ Chat Completion Endpoint ============

@app.post("/v1/chat/completions")
async def chat_completions(request: dict):
    """
    OpenAI-compatible chat completions endpoint
    
    Request body:
    {
        "model": "text-davinci-002-render-sha",
        "messages": [{"role": "user", "content": "Hello!"}],
        "stream": false,
        "conversation_id": "optional-uuid",
        "provider": "optional-override"
    }
    """
    try:
        messages = request.get("messages", [])
        model = request.get("model", "text-davinci-002-render-sha")
        stream = request.get("stream", False)
        conversation_id = request.get("conversation_id", str(uuid4()))
        provider = request.get("provider", LLM_PROVIDER)
        
        if not messages:
            raise HTTPException(status_code=400, detail="Messages required")
        
        # Get or create conversation
        if conversation_id not in conversations:
            conversations[conversation_id] = ConversationContext(conversation_id)
        
        conv = conversations[conversation_id]
        user_message = messages[-1].get("content", "")
        conv.add_message("user", user_message)
        
        # Select the appropriate wrapper
        if provider == "qwen":
            if not QWEN_TOKEN:
                raise HTTPException(status_code=500, detail="QWEN_TOKEN not configured")
            rapper = AsyncQwenRapper(QWEN_TOKEN, model=model)
        else:  # openai
            if not CHATRAPPER_TOKEN:
                raise HTTPException(status_code=500, detail="CHATRAPPER_TOKEN not configured")
            if not AsyncRapper:
                raise HTTPException(status_code=500, detail="chatrapper not installed")
            rapper = AsyncRapper(CHATRAPPER_TOKEN, model=model)
        
        # Handle streaming vs non-streaming
        if stream:
            async def generate():
                try:
                    response_text = ""
                    async for chunk in rapper.stream(user_message):
                        response_text += chunk
                        yield f"data: {json.dumps({'choices': [{'delta': {'content': chunk}}]})}\n\n"
                    
                    conv.add_message("assistant", response_text)
                    db.save_conversation(user_message, response_text)
                    yield f"data: [DONE]\n\n"
                except Exception as e:
                    logger.error(f"Streaming error: {e}")
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
            return StreamingResponse(generate(), media_type="text/event-stream")
        else:
            # Non-streaming response
            response_text = await rapper(user_message)
            conv.add_message("assistant", response_text)
            db.save_conversation(user_message, response_text)
            
            return {
                "id": f"chatcmpl-{uuid4()}",
                "object": "chat.completion",
                "created": int(datetime.now().timestamp()),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": response_text
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": len(user_message.split()),
                    "completion_tokens": len(response_text.split()),
                    "total_tokens": len(user_message.split()) + len(response_text.split())
                }
            }
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============ Conversation Management ============

@app.get("/v1/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation history by ID"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conv = conversations[conversation_id]
    return {
        "conversation_id": conversation_id,
        "messages": conv.messages
    }

@app.delete("/v1/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation"""
    if conversation_id in conversations:
        del conversations[conversation_id]
        return {"status": "deleted", "conversation_id": conversation_id}
    else:
        raise HTTPException(status_code=404, detail="Conversation not found")

@app.get("/v1/conversations")
async def list_conversations():
    """List all active conversations"""
    return {
        "conversations": [
            {
                "id": conv_id,
                "message_count": len(conv.messages)
            }
            for conv_id, conv in conversations.items()
        ]
    }

@app.post("/v1/conversations/{conversation_id}/clear")
async def clear_conversation(conversation_id: str):
    """Clear conversation history"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conversations[conversation_id].messages = []
    return {"status": "cleared", "conversation_id": conversation_id}

# ============ Legacy Endpoints (for backwards compatibility) ============

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to LLMchat2API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "models": "/v1/models"
    }

@app.post("/chat/")
async def legacy_chat(message: str):
    """Legacy chat endpoint (for backwards compatibility)"""
    logger.warning("Using deprecated /chat/ endpoint. Use /v1/chat/completions instead.")
    
    if not message:
        raise HTTPException(status_code=400, detail="Message required")
    
    conversation_id = str(uuid4())
    request_body = {
        "messages": [{"role": "user", "content": message}],
        "model": "text-davinci-002-render-sha" if LLM_PROVIDER == "openai" else "qwen-max",
        "stream": False,
        "conversation_id": conversation_id
    }
    
    return await chat_completions(request_body)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
