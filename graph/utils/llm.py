import os
from langchain.chat_models import init_chat_model

llm = init_chat_model(
    model=os.getenv("LLM_MODEL", "gpt-4o"),
    model_provider=os.getenv("LLM_PROVIDER", "openai"),
    temperature=0,
)