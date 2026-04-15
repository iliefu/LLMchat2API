# QWEN API Reverse Engineering Guide

## Table of Contents

1. [Quick Start](#quick-start)
2. [Browser DevTools Method](#browser-devtools-method)
3. [Automated Analysis](#automated-analysis)
4. [Key Information to Capture](#key-information-to-capture)
5. [Response Formats](#response-formats)
6. [Testing](#testing)
7. [Common Issues](#common-issues)
8. [Implementation Examples](#implementation-examples)
9. [Troubleshooting](#troubleshooting)

---

## Quick Start

To get started with reverse engineering the QWEN API, follow these steps:
1. Clone the repository: `git clone https://github.com/iliefu/LLMchat2API.git`
2. Install necessary dependencies.
3. Explore the API by sending basic requests using tools like Postman or CURL.

## Browser DevTools Method

1. Open your browser and navigate to the target web application.
2. Open DevTools (F12 or right-click -> Inspect).
3. Go to the Network tab and monitor the API calls when performing specific actions in the application.
4. Capture request URLs, headers, payloads, and responses.

## Automated Analysis

Using tools like Fiddler or Burp Suite for automated traffic analysis can simplify the reverse engineering process:
- Set up the tool to capture HTTP/S traffic.
- Analyze the captured requests for patterns and potential vulnerabilities.

## Key Information to Capture

While reverse engineering the API, be attentive to:
- Request and response headers
- HTTP methods (GET, POST, etc.)
- Status codes and response times
- JSON structures in request and response bodies

## Response Formats

Understand the expected formats for API responses:
- Common formats: JSON, XML
- Example response:
  ```json
  {
      "status": "success",
      "data": {
          "id": 1,
          "name": "example"
      }
  }
  ```

## Testing

Perform tests using tools like Postman or a custom script:
1. Set up your test environment with necessary authentication.
2. Send test requests and inspect the responses.
3. Validate the responses against expectations.

## Common Issues

- **Authentication errors**: Ensure correct use of tokens or keys.
- **Rate limiting**: Be aware of API limits and test accordingly.
- **Timeouts**: Increase timeout settings if necessary.

## Implementation Examples

Here are some code snippets to help you implement API calls:

### Example using CURL
```bash
curl -X GET "https://api.qwen.com/data" -H "Authorization: Bearer YOUR_TOKEN"
```

### Example using Python
```python
import requests

url = "https://api.qwen.com/data"
headers = {"Authorization": "Bearer YOUR_TOKEN"}
response = requests.get(url, headers=headers)
print(response.json())
```

## Troubleshooting

- If you receive a 404 error, check the endpoint URL.
- If responses are not as expected, review the request payloads and headers.
- For persistent issues, consult the API documentation or reach out for support.

Quick Action Plan
Step 1: Gather API Information
bash
# Option A: Run automated analyzer
python api_reverse_engineer.py
# (paste your Qwen token when prompted)

# Option B: Manual analysis (follow guide in browser)
# 1. Open https://chat.qwen.ai
# 2. Press F12 → Network tab
# 3. Send a message
# 4. Capture POST request details
Step 2: Document Findings
Create a file qwen_api_info.json:

JSON
{
  "endpoint": "https://chat.qwen.ai/[ACTUAL_PATH]",
  "method": "POST",
  "auth_header": "Authorization: Bearer <token>",
  "request_format": {
    "model": "qwen-max",
    "messages": [{"role": "user", "content": ""}],
    "stream": true
  },
  "response_format": {
    "type": "streaming",
    "delimiter": "data: ",
    "message_path": "choices[0].delta.content"
  },
  "available_models": ["qwen-max", "qwen-plus", "qwen-turbo"]
}
Step 3: Update qwen_wrapper.py
Based on findings:

Python
# Update these values:
self.api_endpoint = "https://chat.qwen.ai/[DISCOVERED_ENDPOINT]"
self.response_field_path = "[MESSAGE_EXTRACTION_PATH]"
self.available_models = ["qwen-max", "qwen-plus", "qwen-turbo"]
Step 4: Test Integration
bash
# Test the wrapper
python -c "
import asyncio
from qwen_wrapper import AsyncQwenRapper
wrapper = AsyncQwenRapper('YOUR_TOKEN', 'qwen-max')
asyncio.run(wrapper('Hello'))
"
🔑 Key Things to Capture
Item	How to Find	Example
Endpoint	Network tab → POST request URL	https://chat.qwen.ai/api/chat
Token	DevTools → Cookies/Headers	eyJhbGci...
Request Body	Network tab → Request	{"messages": [...], "stream": true}
Response	Network tab → Response	data: {"choices":[...]}
Models	API response or UI dropdown	qwen-max, qwen-plus
🚀 Once You Have the API Details
Share what you discover and I'll help you:

✅ Update qwen_wrapper.py
✅ Integrate with server.py
✅ Test the full integration
✅ Add to LLMchat2API repo
