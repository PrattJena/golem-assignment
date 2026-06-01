from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from graph.utils.llm import llm

SYSTEM_PROMPT = """You are an auto parts advisor. Given ranked product recommendations, 
write a helpful response for the customer. Keep the same ranking order. 
Include product name, price, stock status, vehicle compatibility, and reasoning for each."""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        (
            "human",
            "Customer question: {question}\n\nRecommendations:\n{recommendations}",
        ),
    ]
)

stream_response_chain = prompt | llm | StrOutputParser()
