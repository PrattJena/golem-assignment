from dotenv import load_dotenv

load_dotenv()

from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from graph.utils.llm import llm


class ResolvedQuery(BaseModel):
    """
    Intent and standalone question resolved from conversation context.
    """

    intent: Literal["auto_parts", "off_topic"] = Field(
        description="Whether the latest user message is related to auto parts, vehicles, driving, maintenance, or auto part product recommendations."
    )

    resolved_question: str = Field(
        description="Standalone auto parts request. Empty string if the latest user message is off topic."
    )


SYSTEM_PROMPT = """You classify and rewrite customer messages for an auto parts advisor.
Your job:
1. Decide whether the latest user message is related to auto parts, vehicles, driving, maintenance, or auto part product recommendations etc.
2. If the latest message is auto parts related, rewrite it so it can be understood on its own without the conversation history.
3. If it is off-topic, set intent to off_topic and leave resolved_question empty.

Rules:
- Focus on the latest user message first.
- Use the previous resolved auto-parts request as the active context when the latest message is clearly a follow-up, clarification, or constraint.
- If the latest message provides vehicle information and there is a previous resolved auto-parts request, treat it as a follow-up constraint for that request.
- For follow-up constraints, preserve the broad original need and add the new constraint.
- Do not collapse a broad request into only one product family unless the latest user message explicitly asks for that product family.
- Do not turn a general constraint into a question about a specific previously recommended product.
- If the latest message introduces a new vehicle symptom, product need, or shopping request, treat it as a new auto-parts request unless the user clearly connects it to the previous request.
- If the latest message is unrelated to vehicles, auto parts, driving, maintenance, or auto part product recommendations, set intent to off_topic.
- If it is off-topic, set intent to off_topic and leave resolved_question empty.
- Do not generate SQL.
- Do not answer auto parts questions here.
"""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        (
            "human",
            "Previous resolved auto-parts request:\n{previous_resolved_question}\n\nConversation history:\n{history}\n\nLatest user message:\n{question}",
        ),
    ]
)

resolve_query_chain = prompt | llm.with_structured_output(ResolvedQuery)
