from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
import json
from chatrapper import AsyncRapper
import os

app = FastAPI(title="ChatRapper API")

# Initialize with access token from environment
ACCESS_TOKEN = os.environ.get("CHATRAPPER_TOKEN")
if not ACCESS_TOKEN:
    raise ValueError("CHATRAPPER_TOKEN environment variable not set")

@app.post("/v1/chat/completions")
async def chat(request: dict):
    """
    OpenAI-compatible chat endpoint
    {
        "messages": [{"role": "user", "content": "Your question"}],
        "model": "text-davinci-002-render-sha",  # optional
        "stream": true/false  # optional
    }
    """
    try:
        messages = request.get("messages", [])
        if not messages:
            raise HTTPException(status_code=400, detail="Messages required")
        
        user_message = messages[-1].get("content", "")
        model = request.get("model", "text-davinci-002-render-sha")
        stream = request.get("stream", False)
        
        rapper = AsyncRapper(ACCESS_TOKEN, model=model)
        
        if stream:
            return StreamingResponse(
                rapper.stream(user_message),
                media_type="text/event-stream"
            )
        else:
            response = await rapper(user_message)
            return {
                "choices": [{"message": {"role": "assistant", "content": response}}],
                "model": model
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/models")
async def list_models():
    """List available models"""
    return {
        "data": [
            {"id": "text-davinci-002-render-sha", "owned_by": "openai"},
            {"id": "gpt-4", "owned_by": "openai"}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
