"""
Quick setup verification script.
Run this before any experiments to confirm Ollama + AutoGen are working.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from autogen import ConversableAgent
from config.llm_config import OLLAMA_CONFIG

print("Testing AutoGen + Ollama connection...\n")

agent = ConversableAgent(
    name="TestAgent",
    llm_config={"config_list": [OLLAMA_CONFIG]},
    human_input_mode="NEVER",
    max_consecutive_auto_reply=1,
)

# Simple one-shot reply test
reply = agent.generate_reply(
    messages=[{"role": "user", "content": "Say exactly: SETUP_OK"}],
    sender=None,
)

print(f"Agent response: {reply}")
print("\nAutoGen + Ollama setup successful!")
