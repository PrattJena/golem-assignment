import os
from langchain.chat_models import init_chat_model

model_name = os.getenv("LLM_MODEL")
model_provider = os.getenv("LLM_PROVIDER")

llm = init_chat_model(
    model=model_name,
    model_provider=model_provider,
    temperature=0,
)