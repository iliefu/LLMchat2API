# Add import
from qwen_wrapper import AsyncQwenRapper

# Add environment variable for switching
PROVIDER = os.environ.get("LLM_PROVIDER", "openai")  # "openai" or "qwen"

@app.post("/v1/chat/completions")
async def chat_completions(request: dict):
    """OpenAI-compatible endpoint supporting multiple providers"""
    messages = request.get("messages", [])
    model = request.get("model", "text-davinci-002-render-sha")
    stream = request.get("stream", False)
    conversation_id = request.get("conversation_id", str(uuid4()))
    provider = request.get("provider", PROVIDER)  # Allow per-request override
    
    if not messages:
        raise HTTPException(status_code=400, detail="Messages required")
    
    if conversation_id not in conversations:
        conversations[conversation_id] = ConversationContext(conversation_id)
    
    conv = conversations[conversation_id]
    user_message = messages[-1].get("content", "")
    conv.add_message("user", user_message)
    
    # Select rapper based on provider
    if provider == "qwen":
        token = os.environ.get("QWEN_TOKEN")
        if not token:
            raise HTTPException(status_code=500, detail="QWEN_TOKEN not configured")
        rapper = AsyncQwenRapper(token, model=model)
    else:  # openai
        token = os.environ.get("CHATRAPPER_TOKEN")
        if not token:
            raise HTTPException(status_code=500, detail="CHATRAPPER_TOKEN not configured")
        rapper = AsyncRapper(token, model=model)
    
    # Rest of the logic stays the same...
    # (streaming/non-streaming handling)
