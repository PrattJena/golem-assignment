from dotenv import load_dotenv
load_dotenv()

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from graph.utils.llm import llm
from graph.utils.get_inventory_context import get_inventory_context




class SQLQuery(BaseModel):
    """
    SQL query to be executed on the database.
    """

    sql_query: str = Field(
        description="The SQLite SELECT query generated for retrieving candidate products from the inventory table."
    )

SYSTEM_PROMPT = """You are an expert auto parts advisor and SQL specialist. 
Your job is to listen to a customer's vague symptoms or needs, figure out what kind of parts they require, and query the inventory database to find them.

Customers will use everyday language. Use your mechanical knowledge to identify what parts are relevant and then write SQL to find them.

Schema:
    {schema}

Sample rows:
    {sample_rows}


Rules:
    - SELECT only. Never INSERT, UPDATE, DELETE, DROP, or ALTER or any write operation.
    - Only reference columns that exist in the schema above.
    - Use LIKE with wildcards for text matching, not exact equals.
    - Do not LIMIT results. The recommendation step will narrow down later.
    - Include out-of-stock items. Do not filter on stock_quantity.
    - If the user specifies a vehicle type, include parts with "universal" compatibility in addition to the specified type. Universal parts fit all vehicles.

Important SQL construction rules:
    - Cast a wide net for product relevance. Use OR across relevant searchable text columns from the schema, rather than relying on only one column.
    - Separate product-relevance terms from constraints. Product-relevance terms describe the problem, situation, or product type to search for. Constraints narrow the result set, such as vehicle type, budget, brand preference, size, fitment etc.
    - Treat constraints as filters, not relevance signals. Group product-relevance conditions together first, then apply constraints to the entire group.
    """

structured_llm = llm.with_structured_output(SQLQuery)
schema, sample_rows = get_inventory_context()

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        ("human", "{question}"),
    ]
).partial(
    schema=schema,
    sample_rows=sample_rows,
)

generate_sql_chain = prompt | structured_llm

if __name__ == "__main__":
    result = generate_sql_chain.invoke({"question": "My car makes a squealing noise when I brake — what do I need?"})
    print(result)
