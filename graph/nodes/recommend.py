from typing import Dict, Any, List
from graph.state import GraphState
from graph.chains.recommend_parts import recommend_chain
from langchain_core.messages import AIMessage


def format_query_results(query_results: List[Dict[str, Any]]) -> str:
    """Format query results as a readable string for the LLM."""
    if not query_results:
        return "No products found."

    lines = []
    for product in query_results:
        stock = int(product.get("stock_quantity") or 0)
        stock_status = f"{stock} in stock" if stock > 0 else "OUT OF STOCK"

        lines.append(
            f"- [{product.get('sku', 'N/A')}] {product.get('name', 'N/A')} | ${product.get('price', 'N/A')} | {stock_status} | Vehicle: {product.get('vehicle_compatibility', 'N/A')} "
            f"Category: {product.get('category', 'N/A')} | Brand: {product.get('brand', 'N/A')} | Specs: {product.get('key_specs', 'N/A')}"
            f"{product.get('description', 'N/A')}"
        )

    return "\n".join(lines)


def recommend(state: GraphState) -> Dict[str, Any]:
    """
    Takes query results and the original question, produces a ranked recommendation string for the customer.
    """
    question = state["question"]
    query_results = state.get("query_results", [])
    messages = state.get("messages", [])

    if len(messages) > 1:
        # Could limit the history to last 5 messages to save tokens but conversations will not be that long.
        history = "\n".join([f"{m.type}: {m.content}" for m in messages[:-1]])
        question = f"Conversation so far:\n{history}\n\nCurrent question: {question}"

    formatted = format_query_results(query_results)

    result = recommend_chain.invoke({
        "question": question,
        "query_results": formatted,
    })

    output = f"{result.summary}\n\n"
    for i, part in enumerate(result.parts, 1):
        output += f"{i}. {part.name} — ${part.price}, {part.stock_status} | {part.vehicle_compatibility}\n"
        output += f"   {part.reasoning}\n\n"

    return {"generation": output.strip(), "messages": [AIMessage(content=output.strip())],}