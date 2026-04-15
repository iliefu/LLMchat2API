from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # Adjust this as necessary
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

conversation_history = []  # Placeholder for conversation history

@app.get("/")
async def get():
    return HTMLResponse("<html><body><h1>Welcome to the FastAPI Chat Server</h1></body></html>")

@app.post("/chat/")
async def chat(message: str):
    # Here you would normally integrate with OpenAI's API to get a response
    response = f"You said: {message}"
    conversation_history.append({'user': message, 'bot': response})
    return {'response': response, 'history': conversation_history}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        response = f"You said: {data}"
        conversation_history.append({'user': data, 'bot': response})
        await websocket.send_text(response)