from pydantic import BaseModel

class ChatRequest(BaseModel):
    user_id: str
    message: str
    timestamp: str

class ChatResponse(BaseModel):
    response_id: str
    user_id: str
    response_message: str
    timestamp: str
    success: bool
    error: str = None
