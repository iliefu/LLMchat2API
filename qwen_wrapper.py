#!/usr/bin/env python
"""
Qwen Chat Wrapper - Adapts Qwen API for LLMchat2API
Mirrors the AsyncRapper interface from chatrapper but for Qwen
"""

import asyncio
import base64
import json
import typing
from uuid import uuid4

import httpx
import websockets
import logging
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK


class QwenMessageDeserializer:
    """Deserialize Qwen's streaming response format"""
    def __init__(self, data: str) -> None:
        self.data = data.lstrip("data: ").strip()
    
    def __str__(self) -> str:
        try:
            js = json.loads(self.data)
            # Adjust based on actual Qwen response structure
            # This is a placeholder - needs verification
            if 'choices' in js and len(js['choices']) > 0:
                delta = js['choices'][0].get('delta', {})
                return delta.get('content', '')
            elif 'message' in js:
                return js['message']['content']['parts'][0]
            return ""
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logging.error(f"Deserialize error: {e}, data: {self.data}")
            return ""


class AsyncQwenRapper:
    """Async wrapper for Qwen Chat API"""
    
    def __init__(self, 
                 access_token: str,
                 model: str = "qwen-max") -> None:
        """
        Initialize Qwen Chat wrapper
        Args:
            access_token (str): Qwen chat token, acquired from https://chat.qwen.ai/api/auth/session
            model (str): Model name - "qwen-max", "qwen-plus", "qwen-turbo", etc.
        """
        self.access_token = access_token
        self.model = model
        self.base_url = "https://chat.qwen.ai"  # May need adjustment
    
    async def _stream_from_wss(self, chunk: str) -> typing.AsyncGenerator[str, None]:
        """Handle WebSocket streaming if Qwen uses it"""
        try:
            data = json.loads(chunk)
            if 'wss_url' in data:
                url = data['wss_url']
                async with websockets.connect(url) as websocket:
                    while True:
                        try:
                            response = await websocket.recv()
                            body = json.loads(response)["body"]
                            body = base64.b64decode(body).decode('utf-8')
                            if 'DONE' in body:
                                break
                            yield body
                        except (ConnectionClosedOK, ConnectionClosedError):
                            break
        except (json.JSONDecodeError, KeyError):
            logging.warning("WSS streaming not available")
    
    async def stream(self, text: str) -> typing.AsyncGenerator[str, None]:
        """Stream response from Qwen Chat"""
        
        # Qwen request format (needs verification)
        body = {
            "messages": [
                {
                    "role": "user",
                    "content": text
                }
            ],
            "model": self.model,
            "stream": True,
            # Add other Qwen-specific parameters as needed
        }
        
        headers = {
            "accept": "text/event-stream",
            "accept-language": "en-US,en;q=0.9",
            "authorization": f"Bearer {self.access_token}",
            "content-type": "application/json",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "Referer": "https://chat.qwen.ai/",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    'POST',
                    url=f"{self.base_url}/backend-api/conversation",
                    headers=headers,
                    json=body,
                    timeout=60.0
                ) as response:
                    if response.status_code != 200:
                        raise Exception(f"Qwen API error: {response.status_code}")
                    
                    async for chunk in response.aiter_text():
                        chunk = chunk.lstrip("data: ").strip()
                        if chunk and "wss_url" in chunk:
                            async for x in self._stream_from_wss(chunk):
                                yield str(QwenMessageDeserializer(x))
                        elif chunk:
                            yield str(QwenMessageDeserializer(chunk))
        except Exception as e:
            logging.error(f"Qwen streaming error: {e}")
            raise
    
    async def __call__(self, text: str) -> str:
        """Get full response (non-streaming)"""
        prev = ""
        async for x in self.stream(text):
            print(x.replace(prev, ""), end="", flush=True)
            prev = max(prev, x, key=len)
        return prev


class QwenRapper:
    """Synchronous wrapper for Qwen Chat API"""
    
    def __init__(self,
                 access_token: str,
                 model: str = "qwen-max") -> None:
        self._proxy = AsyncQwenRapper(access_token, model)
    
    def __call__(self, text: str) -> str:
        return asyncio.run(self._proxy(text))
