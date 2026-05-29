# Auto Parts Recommendation Agent

An LLM-powered auto parts advisor built with LangGraph. A customer describes their car problem in plain language, and the agent identifies relevant parts from an inventory database, then returns ranked recommendations with explanations.

## How It Works

```
User Question
    ↓
Generate SQL (LLM reasons about the problem → writes SQL)
    ↓
Execute SQL (runs query against SQLite)
    ↓
  error? → retry SQL Generation (up to 3 attempts)
    ↓
Recommend (LLM ranks top 2-3 parts with explanations)
    ↓
Response
```

![Graph](graph.png)

### Architecture & Workflow

1. **Dual-Hat SQL Generation & Self-Correction:** The LLM first acts as an automotive technician to map customer symptoms to parts (e.g., _squealing brakes_ → brake pads), then dynamically generates the corresponding SQL query.
   - **Retry Loop:** If the generated SQL contains syntax errors or fails execution, the graph routes back to the LLM with the error trace for an automatic retry/self-healing step.

2. **Contextual Recommendation:** A separate downstream step ingests the final, validated SQL query results to rank available products and formulate a polished, customer-facing response with clear automotive reasoning.

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- OpenAI API key (default) or [Ollama](https://ollama.com/) for local models

### Installation

```bash
git clone <repo-url>
cd golem-assignment

# Install dependencies
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env and add your API key + model preferences
# LLM_PROVIDER=openai (default) or ollama
# LLM_MODEL=gpt-4o (default) or any supported model

# Initialize the database
uv run python ingest_catalog.py
```

### Run

```bash
uv run python main.py
```

## Google Sheet

**View-only link:** `https://docs.google.com/spreadsheets/d/14nmGgKih11rhUxOprxWXeCIDY2GErNPAy022cOVhP48/edit?usp=sharing`

The product catalog (30 items) lives in a Google Sheet as the source of truth. The sheet has been shared with view-only access so you can inspect and copy it.

On startup, the app fetches the sheet data via the Google Sheets API using a service account, then loads it into a local SQLite database for querying. If you want to test with your own copy, make a copy of the sheet and update `GOOGLE_SHEET_ID` in `.env`. Share it with the service account email found in `service_account.json` under `client_email`.

## Project Structure

```
golem-assignment/
├── graph/
│   ├── chains/
│   │   ├── generate_sql.py       # LLM chain: question + schema → SQL
│   │   └── recommend_parts.py    # LLM chain: query results → ranked recommendations
│   ├── nodes/
│   │   ├── generate.py           # Node: reads state, calls generate_sql chain
│   │   ├── execute.py            # Node: runs SQL against SQLite (no LLM)
│   │   └── recommend.py          # Node: formats results, calls recommend chain
│   ├── utils/
│   │   ├── llm.py                    # Shared LLM instance (configurable via .env)
│   │   └── get_inventory_context.py  # Reads schema + sample rows at import time
│   ├── consts.py                 # Node name constants
│   ├── graph.py                  # StateGraph wiring + conditional edges
│   └── state.py                  # Custom GraphState (TypedDict)
├── ingest_catalog.py             # CSV → SQLite with explicit schema
├── main.py                       # Entry point
├── auto_parts_catalog.csv        # Product catalog (30 items)
└── pyproject.toml
```

## Design Decisions

### Q1) Why Google Sheets API with a Service Account

The assignment offered two ways to read from Google Sheets: a public CSV export or the Google Sheets API with a service account. I chose the service account approach because it keeps the sheet private. Only the service account email needs access, instead of exposing the inventory through a public CSV URL.

The tradeoff is a bit more setup, but it is closer to a real production workflow. In production, this approach also gives better control over access, credential rotation, and auditing.

### Q2) Why Separate Chains and Nodes

I separated chains from nodes to keep the code modular and easier to test. Chains define the LLM behavior, such as the prompt, model, and structured output. Nodes handle graph specific logic, such as reading state, passing inputs to chains, formatting SQL results, and returning state updates.

This keeps the LLM prompts reusable while keeping state management inside the graph nodes.

### Q3) Why Option A: LLM Generates Raw SQL

The assignment offered a few possible approaches. I chose Option A, where the LLM generates SQL directly from the user’s natural language question.

I considered Option B, where the LLM returns structured filters like category, keywords, or price range and the code builds the SQL. That is safer, but it limits the search to fields I define upfront. I also considered a hybrid approac (Option C) where one step extracts intent and another generates SQL, but that adds another node and LLM call.

For this project, Option A felt like the best tradeoff. Auto-parts questions can be vague, like “I’m doing a winter road trip from Boston to Montreal,” where the user may need batteries, wipers, antifreeze, or tires. Letting the LLM generate SQL directly allows it to reason from symptoms to relevant parts in one step, while LangGraph still handles the execution and retry flow around it.

- The SQLite connection is opened in **read-only mode** (`?mode=ro`), so the database itself rejects any write operation regardless of what SQL reaches it.
- The `execute_sql` node rejects any query that doesn't start with `SELECT`.
- Python's `sqlite3.cursor.execute()` only runs a single statement per call, blocking multi-statement injection like `SELECT ...; DROP TABLE ...`.
- The system prompt explicitly instructs the LLM: "SELECT only. Never INSERT, UPDATE, DELETE, DROP, or ALTER."
- **In production**, I would additionally add: a SQL parser/validator to structurally verify queries before execution, and query parameterization where possible.

### Q4) Why Custom State, Not `MessagesState`

I used a custom `TypedDict` because the graph passes structured data between nodes, not just chat messages. The state includes fields like the generated SQL query, SQL errors, database rows, retry count, and final recommendation.

Using `MessagesState` would make this less clear because I would have to wrap structured values inside chat message objects. A custom state keeps the data flow explicit and easier to debug.

### Q5) Why No Tools / @tool Decorator

Tools are useful when the LLM needs to choose an action at runtime, such as listing tables, fetching a schema, or running a query. In this project, there is only one known inventory table, and its schema is already included in the prompt.

Because the workflow is fixed, I let LangGraph control the execution through explicit edges instead of relying on LLM tool-calling decisions. The `execute_sql` step is plain Python logic inside a graph node, not a separate tool.

### Q6) Wide Net SQL Strategy

The system prompt instructs the LLM to use OR across multiple columns (name, category, description, key_specs) and to skip LIMIT. The SQL step casts a wide net to find candidates. The recommendation step narrows down to the top 2-3 products. This avoids losing relevant results to overly tight SQL filters.

## Edge Cases

### 1) Out of Stock

SQL intentionally does not filter on `stock_quantity`. Out-of-stock items are still passed to the recommendation chain because the best technical match may not always be available. The response flags those items clearly and suggests in-stock alternatives when possible.

Because the recommendation chain returns structured output with a `stock_status` field, a production backend could also use that field programmatically, for example to show an out-of-stock badge, trigger reorder alerts, or suggest substitutes without parsing free text.

### 2) Off-Topic Queries

There is no explicit router node. If the user asks "What's the weather?", the LLM still generates SQL (forced by structured output), the query returns empty or irrelevant results, and the recommendation chain responds: "Your question doesn't relate to auto parts." This works because the recommendation prompt includes: "If no products are found, return an empty parts list and explain what the customer likely needs."

A production system would add a **router node** before SQL generation to short-circuit off-topic queries without burning two LLM calls.

### 3) SQL Errors / Retry Loop

If the generated SQL fails to execute (syntax error, wrong column name), the error message is passed back to the `generate_sql` node via state. The LLM sees the error and fixes its SQL. This retries up to 3 times before giving up and routing to the recommendation step with empty results.

## What I'd Do Differently With More Time

- **Multi-turn conversation** — Add `messages` to state with LangGraph's persistence layer (`MemorySaver`) so the user can ask followups like "what about for my SUV?" without re-stating the problem.

- **Router node** — Short circuit off-topic queries before SQL generation. Saves two LLM calls on irrelevant inputs.

- **SQL validation** — Use `sqlglot` to parse and validate SQL structurally before execution, catching more issues than the `startswith("SELECT")` check.

- **Structured logging** — Replace `print` statements with proper logging for production traceability.

- **Tests** — Unit tests for each chain in isolation, integration tests for the full graph with known queries and expected results.
