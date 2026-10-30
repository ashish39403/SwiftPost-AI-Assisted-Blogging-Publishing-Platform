from langchain_core.prompts import ChatPromptTemplate

from apps.anna.interfaces.llm import ChatMessage, GenerationRequest
from apps.anna.prompts import REVIEW_SYSTEM, review_user_prompt
from apps.composer.prompts import COMPOSE_SYSTEM, compose_user_prompt, revise_user_prompt

_COMPOSE_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", COMPOSE_SYSTEM),
        ("human", "{instruction}"),
    ]
)

_REVIEW_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", REVIEW_SYSTEM),
        ("human", "{instruction}"),
    ]
)


def compose_request(title: str, *, current_title="", current_excerpt="", current_body="", instruction="") -> GenerationRequest:
    prompt = (
        revise_user_prompt(current_title, current_excerpt, current_body, instruction)
        if current_body and instruction
        else compose_user_prompt(title)
    )
    messages = _COMPOSE_PROMPT.format_messages(instruction=prompt)
    return GenerationRequest(
        kind="compose",
        messages=_to_chat(messages),
        max_tokens=4096,
        timeout=120.0,
    )


def review_request(title: str, excerpt: str, body: str) -> GenerationRequest:
    messages = _REVIEW_PROMPT.format_messages(
        instruction=review_user_prompt(title, excerpt, body)
    )
    return GenerationRequest(
        kind="review",
        messages=_to_chat(messages),
        max_tokens=2800,
        timeout=180.0,
    )


def _to_chat(messages):
    converted = []
    for item in messages:
        role = {"system": "system", "human": "user", "ai": "assistant"}.get(item.type, "user")
        converted.append(ChatMessage(role=role, content=str(item.content)))
    return converted
