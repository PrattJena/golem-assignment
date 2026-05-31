from dotenv import load_dotenv
load_dotenv()

from graph.utils.llm import llm
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List




class Part(BaseModel):
    name: str = Field(description="Name of the auto part")
    price: float = Field(description="Price of the auto part")
    stock_status: str = Field(description="'In Stock' or 'Out of Stock'")
    vehicle_compatibility: str = Field(description="Vehicle compatibility information")
    reasoning: str = Field(description="Why this auto part fits the customer's problem")


class Recommendation(BaseModel):
    """
    Ranked auto part recommendations for the customer based on their problem.
    """
    parts: List[Part] = Field(description="Top 2-3 recommended auto parts, ranked by relevance")
    summary: str = Field(description="Overall advice to the customer")


SYSTEM_PROMPT = """You are an expert auto parts advisor. 
Given a customer's question and a list of products from our inventory, 
rank the top 2-3 most relevant products and explain why each fits their situation.

Rules:
    - Use your automotive knowledge to explain WHY each part solves their problem.
    - Only recommend products that appear in the provided inventory results.
    - Do not invent products, brands, prices, or specs.
    - If a product is out of stock (stock_quantity = 0), still recommend it if it's the best fit but flag it clearly and suggest an in-stock alternative from the results if one exists.
    - Include price, stock quantity, and key specs in your reasoning.
    - Rank by relevance to the customer's problem, not by price.
    - If no products are found, return an empty parts list. In the summary, explain what type of part the customer likely needs, clearly say that no matching product was found in the current inventory, and suggest they try describing the problem differently.
    - If the question is unrelated to auto parts or vehicles, do not answer it. Simply say you can only help with auto parts and ask the customer to describe their vehicle issue.
    - If the best product for the customer's need is out of stock or incompatible, explicitly mention the closest alternative from the results, even if it falls outside the top 3.
"""

structured_llm = llm.with_structured_output(Recommendation)

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "Customer question: {question}\n\nProducts found:\n{query_results}"),
])

recommend_chain = prompt | structured_llm