from openai import OpenAI

# Point OpenAI client to local API
client = OpenAI(api_key="local", base_url="http://localhost:8000/v1")

# Example 1: Simple chat
response = client.chat.completions.create(
    model="text-davinci-002-render-sha",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)

# Example 2: Streaming
stream = client.chat.completions.create(
    model="text-davinci-002-render-sha",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True
)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
