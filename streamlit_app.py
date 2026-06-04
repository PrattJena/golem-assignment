from dotenv import load_dotenv

load_dotenv()

import uuid
from typing import Any, Dict

import streamlit as st

st.set_page_config(
    page_title="Auto Parts Advisor",
    page_icon="🚗",
    layout="wide",
)


@st.cache_resource
def bootstrap_app():
    """
    Initialize the inventory database once and import the LangGraph runner
    and streaming chain. Avoids re-syncing on every Streamlit rerun.
    Handles secrets for Streamlit Cloud deployment.
    """
    import json
    import os
    import tempfile

    # Handle Google service account from Streamlit Secrets
    if "GOOGLE_SERVICE_ACCOUNT" in st.secrets:
        creds = json.dumps(dict(st.secrets["GOOGLE_SERVICE_ACCOUNT"]))
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        tmp.write(creds)
        tmp.close()
        os.environ["GOOGLE_SHEETS_CREDENTIALS_PATH"] = tmp.name

    # Set env vars from Streamlit Secrets
    for key in [
        "OPENAI_API_KEY",
        "GOOGLE_SHEET_ID",
        "INVENTORY_DB_PATH",
        "LLM_MODEL",
        "LLM_PROVIDER",
    ]:
        if key in st.secrets and key not in os.environ:
            os.environ[key] = st.secrets[key]

    from graph.agent import stream_agent
    from graph.chains.stream_response import stream_response_chain

    return stream_agent, stream_response_chain


stream_agent, stream_response_chain = bootstrap_app()


def create_chat() -> str:
    chat_id = str(uuid.uuid4())
    st.session_state.chats[chat_id] = {
        "title": "New Chat",
        "thread_id": chat_id,
        "messages": [],
    }
    st.session_state.current_chat_id = chat_id
    return chat_id


def init_session_state() -> None:
    if "chats" not in st.session_state:
        st.session_state.chats = {}
    if "current_chat_id" not in st.session_state:
        create_chat()


def get_current_chat() -> Dict[str, Any]:
    return st.session_state.chats[st.session_state.current_chat_id]


def update_chat_title(chat: Dict[str, Any], user_message: str) -> None:
    if chat["title"] == "New Chat":
        title = user_message.strip()
        chat["title"] = title[:40] + ("..." if len(title) > 40 else "")


def run_graph_with_status(user_message: str, thread_id: str) -> tuple[str, str, bool]:
    """
    Run the LangGraph agent with progress indicators.
    Returns (generation, resolved_question, should_stream).
    """
    generation = ""
    resolved_question = ""

    with st.status("Working on your request...", expanded=True) as status:
        for node_name, output in stream_agent(user_message, thread_id):
            if node_name == "resolve_query":
                intent = output.get("intent", "")
                resolved_question = output.get("resolved_question", "")
                status.write(f"✓ Understanding your question... (intent: {intent})")

                if intent == "off_topic":
                    status.update(label="Done", state="complete", expanded=False)
                    return output.get("generation", ""), "", False

            elif node_name == "generate_sql":
                status.write("✓ Searching inventory...")

            elif node_name == "execute_sql":
                results = output.get("query_results", [])
                error = output.get("error_message", "")
                if error:
                    status.write(f"✓ Query error: {error}")
                else:
                    status.write(f"✓ Found {len(results)} matching products")

            elif node_name == "recommend":
                generation = output.get("generation", "")
                status.write("✓ Generating recommendations...")

        status.update(label="Done", state="complete", expanded=False)

    return generation, resolved_question, True


# App layout
init_session_state()

st.sidebar.title("Auto Parts Advisor")

if st.sidebar.button("+ New Chat", use_container_width=True):
    create_chat()
    st.rerun()

st.sidebar.divider()
st.sidebar.caption("Conversations")

for chat_id, chat in reversed(list(st.session_state.chats.items())):
    is_active = chat_id == st.session_state.current_chat_id
    label = f"→ {chat['title']}" if is_active else chat["title"]
    if st.sidebar.button(label, key=f"chat-{chat_id}", use_container_width=True):
        st.session_state.current_chat_id = chat_id
        st.rerun()

current_chat = get_current_chat()

st.title("🚗 Auto Parts Advisor")
st.caption(
    "Describe a vehicle issue, trip, or part need. I'll search the inventory and recommend relevant products."
)

for msg in current_chat["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_prompt := st.chat_input("Describe your vehicle issue or what you need..."):
    update_chat_title(current_chat, user_prompt)

    current_chat["messages"].append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        generation, resolved_question, should_stream = run_graph_with_status(
            user_message=user_prompt,
            thread_id=current_chat["thread_id"],
        )

        if not generation:
            fallback = "Sorry, I could not generate a response."
            st.markdown(fallback)
            current_chat["messages"].append({"role": "assistant", "content": fallback})

        elif not should_stream:
            st.markdown(generation)
            current_chat["messages"].append(
                {"role": "assistant", "content": generation}
            )

        else:
            if "No products found" in generation or not any(
                line.strip().startswith(("1.", "2.", "3.")) for line in generation.split("\n")
            ):
                st.markdown(generation)
                current_chat["messages"].append({"role": "assistant", "content": generation})
            else:
                question = resolved_question or user_prompt
                response_placeholder = st.empty()
                full_response = ""

                try:
                    for chunk in stream_response_chain.stream({
                        "question": question,
                        "recommendations": generation,
                    }):
                        full_response += chunk
                        response_placeholder.markdown(full_response)

                    current_chat["messages"].append({
                        "role": "assistant",
                        "content": full_response,
                    })

                except Exception:
                    response_placeholder.markdown(generation)
                    current_chat["messages"].append({
                        "role": "assistant",
                        "content": generation,
                    })