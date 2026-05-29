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
    - Use LIKE with wildcards for text matching (e.g., LIKE '%pad%'), not exact equals.
    - Cast a wide net. Use OR across multiple columns (name, category, description, key_specs) to find as many potentially relevant products as possible.
    - Do not LIMIT results. The recommendation step will narrow down later.
    - Include out-of-stock items. Do not filter on stock_quantity.
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
