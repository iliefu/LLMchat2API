from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import json
from uuid import uuid4
from datetime import datetime
from typing import List

try:
    from chatrapper import AsyncRapper
except ImportError:
    raise ImportError("Install chatrapper: pip install git+https://github.com/ultrasev/chatrapper.git")

app = FastAPI(title="LLMchat2API", version="1.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

CHATRAPPER_TOKEN = os.environ.get("CHATRAPPER_TOKEN")
if not CHATRAPPER_TOKEN:
    raise ValueError("CHATRAPPER_TOKEN not set")

conversations = {}

class ConversationContext:
    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id
        self.messages: List[dict] = []
    
    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/v1/models")
async def list_models():
    return {"data": [
        {"id": "text-davinci-002-render-sha", "owned_by": "openai"},
        {"id": "gpt-4", "owned_by": "openai"}
    ]}

@app.post("/v1/chat/completions")
async def chat_completions(request: dict):
    messages = request.get("messages", [])
    model = request.get("model", "text-davinci-002-render-sha")
    stream = request.get("stream", False)
    conversation_id = request.get("conversation_id", str(uuid4()))
    
    if not messages:
        raise HTTPException(status_code=400, detail="Messages required")
    
    if conversation_id not in conversations:
        conversations[conversation_id] = ConversationContext(conversation_id)
    
    conv = conversations[conversation_id]
    user_message = messages[-1].get("content", "")
    conv.add_message("user", user_message)
    
    rapper = AsyncRapper(CHATRAPPER_TOKEN, model=model)
    
    if stream:
        async def generate():
            response_text = ""
            async for chunk in rapper.stream(user_message):
                response_text += chunk
                yield f"data: {json.dumps({'choices': [{'delta': {'content': chunk}}]})}\n\n"
            conv.add_message("assistant", response_text)
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(generate(), media_type="text/event-stream")
    else:
        response_text = await rapper(user_message)
        conv.add_message("assistant", response_text)
        return {
            "id": f"chatcmpl-{uuid4()}",
            "object": "chat.completion",
            "created": int(datetime.now().timestamp()),
            "model": model,
            "choices": [{"message": {"role": "assistant", "content": response_text}, "finish_reason": "stop"}]
        }

@app.get("/v1/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"id": conversation_id, "messages": conversations[conversation_id].messages}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
