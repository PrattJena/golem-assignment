from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from graph.utils.llm import llm

SYSTEM_PROMPT = """You are an auto parts advisor. Given ranked product recommendations, 
write a helpful response for the customer. Keep the same ranking order. 
Include product name, price, stock status, vehicle compatibility, and reasoning for each.

Critical rules:
- Only mention products that appear in the provided recommendations.
- Do not invent products, prices, or specs.
- If no products are listed, say so clearly. Do not make up alternatives.
- Preserve exact product names and prices from the input."""

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
