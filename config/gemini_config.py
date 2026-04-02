"""
LLM Configuration for OpenRouter API (OpenAI-compatible endpoint)

Free models available at: https://openrouter.ai/models?q=free

API key is read from:
  - Streamlit secrets  (cloud deploy): st.secrets["OPENROUTER_API_KEY"]
  - Environment variable (local):      OPENROUTER_API_KEY
  - .streamlit/secrets.toml (local):   OPENROUTER_API_KEY = "sk-or-..."
"""

import os

try:
    import streamlit as st
    GEMINI_API_KEY = st.secrets.get("OPENROUTER_API_KEY", os.environ.get("OPENROUTER_API_KEY", ""))
except Exception:
    GEMINI_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

GEMINI_CONFIG = {
    "model": "liquid/lfm-2.5-1.2b-instruct:free",
    "base_url": "https://openrouter.ai/api/v1/",
    "api_key": GEMINI_API_KEY,
    "timeout": 30,
    "temperature": 0.1,
    "max_tokens": 120,
}
