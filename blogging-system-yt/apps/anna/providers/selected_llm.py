import json
import os
import sys

from django.conf import settings
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser

from apps.anna.exceptions import ProviderNotConfigured, ProviderUnavailable
from apps.anna.interfaces.llm import GenerationRequest, ProviderGenerationResult
from apps.anna.providers.model_config import (
    DEFAULT_MODEL,
    chat_options,
    clean_model_id,
    model_for_kind,
)

_ROLE = {
    "system": SystemMessage,
    "user": HumanMessage,
    "assistant": AIMessage,
}


def _running_django_tests():
    return "test" in sys.argv and os.environ.get("ANNA_LIVE_PROVIDER_TEST") != "1"


class OpenAICompatibleLLM:
    """LangChain ChatOpenAI adapter for the configured OpenAI-compatible base URL."""

    def generate(self, request: GenerationRequest) -> ProviderGenerationResult:
        key = settings.AI_PROVIDER_API_KEY
        base = settings.AI_PROVIDER_BASE_URL
        model = model_for(request.kind)
        if not key or not base:
            raise ProviderNotConfigured("The writing model is not configured.")
        if _running_django_tests():
            raise ProviderUnavailable("Live model calls are disabled during automated tests.")

        chat = _chat_model(model=model, key=key, base=base, request=request)
        messages = [_ROLE.get(item.role, HumanMessage)(content=item.content) for item in request.messages]
        try:
            result = chat.invoke(messages)
            text = _content_text(getattr(result, "content", result))
            if request.kind == "compose":
                text = _as_article_json(text)
                if not _has_article_keys(text):
                    repair = messages + [
                        HumanMessage(
                            content="Return JSON only with keys title, excerpt, and body. No markdown."
                        )
                    ]
                    result = chat.invoke(repair)
                    text = _as_article_json(_content_text(getattr(result, "content", result)))
        except ProviderUnavailable:
            raise
        except Exception as exc:
            raise ProviderUnavailable(_safe_provider_error(exc)) from exc

        if not text:
            raise ProviderUnavailable("The writing model returned empty text.")
        return ProviderGenerationResult(text=text, model=model)


def model_for(kind):
    return model_for_kind(
        kind,
        compose=settings.AI_MODEL_COMPOSE,
        review=settings.AI_MODEL_REVIEW,
        fallback=settings.AI_MODEL or DEFAULT_MODEL,
    )


def _chat_model(*, model, key, base, request):
    from langchain_openai import ChatOpenAI

    kwargs = chat_options(
        request.kind,
        model,
        max_tokens=request.max_tokens,
        timeout=request.timeout,
    )
    kwargs["api_key"] = key
    kwargs["base_url"] = base
    try:
        chat = ChatOpenAI(**kwargs)
    except TypeError:
        kwargs.pop("use_responses_api", None)
        chat = ChatOpenAI(**kwargs)
    if request.kind == "compose" and _supports_json_object(model):
        try:
            chat = chat.bind(response_format={"type": "json_object"})
        except Exception:
            pass
    return chat


def _supports_json_object(model):
    name = clean_model_id(model).lower()
    return "gpt-4o" in name or "gpt-4.1" in name


def _content_text(content):
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(str(item.get("text") or ""))
            else:
                parts.append(str(getattr(item, "text", "") or ""))
        return "".join(parts).strip()
    return str(content or "").strip()


def _as_article_json(text):
    try:
        parsed = JsonOutputParser().parse(text)
    except Exception:
        parsed = _extract_object(text)
    if not isinstance(parsed, dict):
        return text
    return json.dumps(
        {
            "title": str(parsed.get("title") or "").strip(),
            "excerpt": str(parsed.get("excerpt") or "").strip(),
            "body": str(parsed.get("body") or "").strip(),
        }
    )


def _extract_object(text):
    raw = (text or "").strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        return json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return None


def _has_article_keys(text):
    try:
        payload = json.loads(text)
    except (TypeError, json.JSONDecodeError):
        return False
    return bool(isinstance(payload, dict) and payload.get("title") and payload.get("excerpt") and payload.get("body"))


def _safe_provider_error(exc):
    text = str(exc).lower()
    if "timeout" in text:
        return "The writing model timed out."
    if "429" in text or "rate" in text:
        return "The writing model is busy. Try again in a moment."
    if "401" in text or "403" in text or "invalid api" in text:
        return "The writing model rejected the API key."
    if "model" in text and ("not found" in text or "does not exist" in text):
        return "That writing model is not available on this provider."
    return "The writing model could not complete the request."
