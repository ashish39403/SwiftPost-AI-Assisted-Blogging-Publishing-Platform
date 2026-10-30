"""Task → model mapping. Provider SDKs stay in the LLM adapter."""

DEFAULT_MODEL = "openai/gpt-5.4-mini"
DEFAULT_COMPOSE = "nvidia/nemotron-3-super-120b-a12b"
DEFAULT_REVIEW = "openai/gpt-5.5"

_REASONING_MARKERS = ("gpt-5", "o1-", "o3-", "o4-", "/o1", "/o3", "/o4", "reasoner")


def clean_model_id(value):
    return (value or "").strip().strip('"').strip("'")


def model_for_kind(kind, *, compose="", review="", fallback=""):
    base = clean_model_id(fallback) or DEFAULT_MODEL
    if kind == "compose":
        return clean_model_id(compose) or clean_model_id(fallback) or DEFAULT_COMPOSE
    if kind == "review":
        return clean_model_id(review) or clean_model_id(fallback) or DEFAULT_REVIEW
    return base


def is_reasoning_model(model):
    name = f"/{clean_model_id(model).lower()}"
    return any(marker in name for marker in _REASONING_MARKERS)


def chat_options(kind, model, *, max_tokens, timeout):
    reasoning = is_reasoning_model(model)
    options = {
        "model": clean_model_id(model),
        "timeout": timeout,
        "max_retries": 1,
        "use_responses_api": False,
        "max_completion_tokens": max_tokens,
    }
    if not reasoning:
        options["temperature"] = 0.7 if kind == "compose" else 0.25 if kind == "review" else 0.4
    return options
