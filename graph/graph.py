from dotenv import load_dotenv

load_dotenv()

from langgraph.graph import END, START, StateGraph

from graph.consts import EXECUTE_SQL, GENERATE_SQL, RECOMMEND, RESOLVE_QUERY
from graph.nodes.execute import execute_sql
from graph.nodes.generate import generate_sql_node
from graph.nodes.recommend import recommend
from graph.nodes.resolve import resolve_query_node
from graph.state import GraphState

MAX_ATTEMPTS = 3


def route_after_resolve(state: GraphState) -> str:
    """
    Route off topic questions directly to END.
    Route auto parts questions to SQL generation.
    """
    if state.get("intent") == "off_topic":
        return END
    return GENERATE_SQL


def route_after_execute(state: GraphState) -> str:
    """
    Route to generate_sql if SQL failed and attempts are still available.
    Otherwise, continue to recommend.
    """
    error_message = state.get("error_message", "")
    retry_count = state.get("retry_count", 0)

    if error_message and retry_count < MAX_ATTEMPTS:
        return GENERATE_SQL

    return RECOMMEND


workflow = StateGraph(GraphState)

workflow.add_node(RESOLVE_QUERY, resolve_query_node)
workflow.add_node(GENERATE_SQL, generate_sql_node)
workflow.add_node(EXECUTE_SQL, execute_sql)
workflow.add_node(RECOMMEND, recommend)

workflow.add_edge(START, RESOLVE_QUERY)

workflow.add_conditional_edges(
    RESOLVE_QUERY,
    route_after_resolve,
    {
        GENERATE_SQL: GENERATE_SQL,
        END: END,
    },
)

workflow.add_edge(GENERATE_SQL, EXECUTE_SQL)

workflow.add_conditional_edges(
    EXECUTE_SQL,
    route_after_execute,
    {
        GENERATE_SQL: GENERATE_SQL,
        RECOMMEND: RECOMMEND,
    },
)

workflow.add_edge(RECOMMEND, END)

if __name__ == "__main__":
    workflow.compile().get_graph().draw_mermaid_png(output_file_path="graph.png")
