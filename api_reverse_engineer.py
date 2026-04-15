"""
API Reverse Engineering Tool for Qwen Chat
This script helps discover and document Qwen's API structure
"""

import asyncio
import json
import httpx
import logging
from datetime import datetime

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class QwenAPIAnalyzer:
    """Analyze and document Qwen Chat API responses"""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.session = httpx.AsyncClient()
        self.api_endpoints = {}
        self.request_formats = {}
        self.response_formats = {}
    
    async def test_endpoint(self, endpoint: str, method: str = "POST", payload: dict = None):
        """Test an endpoint and capture response"""
        headers = {
            "authorization": f"Bearer {self.access_token}",
            "content-type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        print(f"\n{'='*80}")
        print(f"Testing: {method} {endpoint}")
        print(f"{'='*80}")
        
        try:
            if method == "GET":
                response = await self.session.get(endpoint, headers=headers)
            elif method == "POST":
                response = await self.session.post(
                    endpoint,
                    headers=headers,
                    json=payload,
                    timeout=10.0
                )
            
            print(f"Status Code: {response.status_code}")
            print(f"\nResponse Headers:")
            for key, value in response.headers.items():
                print(f"  {key}: {value}")
            
            try:
                data = response.json()
                print(f"\nResponse Body (JSON):")
                print(json.dumps(data, indent=2)[:2000])  # First 2000 chars
                return {
                    "endpoint": endpoint,
                    "method": method,
                    "status": response.status_code,
                    "headers": dict(response.headers),
                    "body": data
                }
            except:
                print(f"\nResponse Body (Text):")
                print(response.text[:500])
                return {
                    "endpoint": endpoint,
                    "method": method,
                    "status": response.status_code,
                    "headers": dict(response.headers),
                    "body": response.text[:500]
                }
        except Exception as e:
            print(f"Error: {e}")
            return {"error": str(e)}
    
    async def test_chat_endpoint(self, message: str, model: str = "qwen-max"):
        """Test the chat completion endpoint"""
        print(f"\n{'#'*80}")
        print(f"# Testing Chat Endpoint with Message: {message}")
        print(f"{'#'*80}")
        
        endpoints_to_test = [
            # Most likely endpoints
            "https://chat.qwen.ai/api/chat",
            "https://chat.qwen.ai/backend-api/conversation",
            "https://chat.qwen.ai/api/conversation",
            "https://chat.qwen.ai/api/v1/chat/completions",
        ]
        
        # Test different payload formats
        payloads = [
            # Format 1: OpenAI-style
            {
                "model": model,
                "messages": [{"role": "user", "content": message}],
                "stream": False
            },
            # Format 2: Qwen-style (guess)
            {
                "model": model,
                "prompt": message,
                "stream": False
            },
            # Format 3: Detailed
            {
                "model": model,
                "messages": [
                    {"role": "user", "content": message}
                ],
                "temperature": 0.7,
                "top_p": 0.95,
                "stream": False
            }
        ]
        
        for endpoint in endpoints_to_test:
            for i, payload in enumerate(payloads):
                result = await self.test_endpoint(endpoint, "POST", payload)
                if result.get("status") == 200:
                    logger.info(f"✓ Found working endpoint: {endpoint} with payload #{i+1}")
                    return result
        
        return None
    
    async def discover_models(self):
        """Discover available models"""
        print(f"\n{'#'*80}")
        print(f"# Discovering Available Models")
        print(f"{'#'*80}")
        
        model_endpoints = [
            "https://chat.qwen.ai/api/models",
            "https://chat.qwen.ai/backend-api/models",
            "https://chat.qwen.ai/v1/models",
        ]
        
        for endpoint in model_endpoints:
            result = await self.test_endpoint(endpoint, "GET")
            if result.get("status") == 200:
                print(f"✓ Found models endpoint: {endpoint}")
                return result
        
        return None
    
    async def test_streaming(self, message: str, model: str = "qwen-max"):
        """Test streaming endpoint"""
        print(f"\n{'#'*80}")
        print(f"# Testing Streaming Response")
        print(f"{'#'*80}")
        
        headers = {
            "authorization": f"Bearer {self.access_token}",
            "content-type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "accept": "text/event-stream"
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": message}],
            "stream": True
        }
        
        endpoints = [
            "https://chat.qwen.ai/api/chat",
            "https://chat.qwen.ai/backend-api/conversation",
        ]
        
        for endpoint in endpoints:
            try:
                print(f"\nTesting streaming: {endpoint}")
                async with self.session.stream("POST", endpoint, json=payload, headers=headers) as response:
                    print(f"Status: {response.status_code}")
                    count = 0
                    async for line in response.aiter_lines():
                        if line.strip():
                            print(f"  Chunk {count}: {line[:100]}")
                            count += 1
                            if count >= 5:  # Only show first 5 chunks
                                break
                    if count > 0:
                        print(f"✓ Streaming works! Got {count}+ chunks")
                        return True
            except Exception as e:
                print(f"  Error: {e}")
        
        return False
    
    async def analyze_auth_session(self):
        """Analyze auth session endpoint"""
        print(f"\n{'#'*80}")
        print(f"# Analyzing Auth Session")
        print(f"{'#'*80}")
        
        result = await self.test_endpoint("https://chat.qwen.ai/api/auth/session", "GET")
        return result
    
    async def run_full_analysis(self):
        """Run complete API analysis"""
        print("\n" + "="*80)
        print("QWEN CHAT API REVERSE ENGINEERING")
        print(f"Started: {datetime.now().isoformat()}")
        print("="*80)
        
        # Test authentication
        print("\n[1/5] Testing authentication...")
        await self.analyze_auth_session()
        
        # Discover models
        print("\n[2/5] Discovering available models...")
        await self.discover_models()
        
        # Test chat endpoint
        print("\n[3/5] Testing chat endpoint...")
        await self.test_chat_endpoint("Hello, what is your name?")
        
        # Test streaming
        print("\n[4/5] Testing streaming response...")
        await self.test_streaming("Tell me a short story")
        
        print("\n[5/5] Complete!")
        print("="*80)
        print("Analysis complete. Check the output above for working endpoints and formats.")
        print("="*80)
    
    async def close(self):
        await self.session.aclose()


# Browser DevTools Network Tab Capture Helper
DEVTOOLS_CAPTURE_TEMPLATE = """
BROWSER DEVTOOLS NETWORK TAB ANALYSIS GUIDE
============================================

1. Open https://chat.qwen.ai in your browser
2. Open DevTools (F12)
3. Go to Network tab
4. Send a message in the chat
5. Look for the network request (usually POST)
6. Click on it and capture the following:

REQUEST DETAILS:
- URL: ___________________________________
- Method: GET / POST / WebSocket
- Headers:
  * Authorization: ___________________________________
  * Content-Type: ___________________________________
  * Other important headers: ___________________________________

REQUEST BODY (copy entire JSON):
___________________________________
___________________________________
___________________________________

RESPONSE DETAILS:
- Status Code: ___
- Content-Type: ___________________________________

RESPONSE BODY (first chunk):
___________________________________
___________________________________
___________________________________

STREAMING FORMAT (if applicable):
- Are responses chunked? Yes/No
- Format: SSE (Server-Sent Events) / WebSocket / Other: ___
- Each chunk starts with: ___________________________________
- Content structure: ___________________________________

RESPONSE STRUCTURE EXAMPLE:
{
  "field1": "...",
  "field2": {
    "message": {
      "content": "...",
      "role": "..."
    }
  }
}

Share this information for API integration!
"""

# Run analysis
async def main():
    # Replace with actual Qwen token
    TOKEN = input("Enter your Qwen API token: ").strip()
    
    if not TOKEN:
        print("Error: Token required")
        print("\nTo get your token:")
        print("1. Open https://chat.qwen.ai")
        print("2. Open browser DevTools (F12)")
        print("3. Go to Application/Storage > Cookies")
        print("4. Look for auth-related tokens")
        return
    
    analyzer = QwenAPIAnalyzer(TOKEN)
    
    try:
        await analyzer.run_full_analysis()
    finally:
        await analyzer.close()

if __name__ == "__main__":
    print(DEVTOOLS_CAPTURE_TEMPLATE)
    print("\n" + "="*80 + "\n")
    asyncio.run(main())
