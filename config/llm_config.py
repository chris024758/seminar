"""
LLM Configuration for Ollama
"""

OLLAMA_CONFIG = {
    "model": "phi3:mini",
    "base_url": "http://localhost:11434/v1",
    "api_key": "ollama",
    "timeout": 60,
    "temperature": 0.1,
    "max_tokens": 50,
    "extra_body": {"num_ctx": 512},
}

ALTERNATIVE_MODELS = {
    "smaller": "phi3:mini",
    "medium": "llama3.1:8b",
    "larger": "mistral:7b",
}

def get_config(model_size="smaller"):
    config = OLLAMA_CONFIG.copy()
    config["model"] = ALTERNATIVE_MODELS[model_size]
    return config
