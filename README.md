# LLMchat2API Quick Start Instructions:
# Clone and setup
git clone https://github.com/iliefu/LLMchat2API.git
cd LLMchat2API

# Set token
export CHATRAPPER_TOKEN="your_chatgpt_token_here"

# Install dependencies
pip install -r requirements.txt

# Run server
python server.py

# Test with OpenAI client
pip install openai
python example_usage.py
