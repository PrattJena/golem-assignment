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
    Takes query results and the resolved question, produces a ranked recommendation string for the customer.
    """
    question = state.get("resolved_question") or state["question"]
    query_results = state.get("query_results", [])

    formatted = format_query_results(query_results)

    result = recommend_chain.invoke({
        "question": question,
        "query_results": formatted,
    })

    output = f"{result.summary}\n\n"
    for i, part in enumerate(result.parts, 1):
        output += f"{i}. {part.name} — ${part.price}, {part.stock_status} | {part.vehicle_compatibility}\n"
        output += f"   {part.reasoning}\n\n"

    assistant_memory = result.summary + "\n\nOptions shown:\n"
    for i, part in enumerate(result.parts, 1):
        assistant_memory += (
            f"{i}. {part.name} — ${part.price}, "
            f"{part.stock_status} | {part.vehicle_compatibility}\n"
        )

    return {
        "generation": output.strip(),
        "messages": [AIMessage(content=assistant_memory.strip())],
    }