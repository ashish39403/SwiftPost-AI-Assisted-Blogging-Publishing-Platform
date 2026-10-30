import re

from apps.anna.exceptions import (
    ProviderBudgetExceeded,
    ProviderNotConfigured,
    ProviderUnavailable,
)
from apps.anna.interfaces.search import SearchResult
from apps.anna.providers import get_search_provider

_SEARCH_HINTS = (
    "search",
    "research",
    "sources",
    "latest",
    "today",
    "current",
    "news",
    "live",
    "according to",
    "2024",
    "2025",
    "2026",
    "cite",
    "reference",
)

_WRITE_HINTS = (
    "write",
    "blog",
    "article",
    "draft",
    "compose",
    "rewrite",
    "paste",
    "full post",
    "deep",
)


def needs_live_search(text, *, writing=False):
    blob = (text or "").lower()
    if writing:
        return True
    if len(blob) >= 400:
        return True
    return any(hint in blob for hint in _SEARCH_HINTS)


def collect_sources(query, *, limit=5, depth="basic"):
    cleaned = re.sub(r"\s+", " ", (query or "").strip())[:300]
    if not cleaned:
        return []
    try:
        provider = get_search_provider()
        return provider.search(cleaned, limit=limit, depth=depth)
    except TypeError:
        try:
            return get_search_provider().search(cleaned, limit=limit)
        except (ProviderNotConfigured, ProviderUnavailable, ProviderBudgetExceeded):
            return []
    except (ProviderNotConfigured, ProviderUnavailable, ProviderBudgetExceeded):
        return []


def collect_images(query, *, limit=6):
    cleaned = re.sub(r"\s+", " ", (query or "").strip())[:300]
    if not cleaned:
        return []
    try:
        provider = get_search_provider()
        search_images = getattr(provider, "search_images", None)
        if not callable(search_images):
            return []
        return list(search_images(cleaned, limit=limit))
    except (ProviderNotConfigured, ProviderUnavailable, ProviderBudgetExceeded, TypeError):
        return []


def format_sources(results: list[SearchResult]):
    if not results:
        return "No live sources were retrieved."
    lines = []
    for index, item in enumerate(results, start=1):
        lines.append(f"{index}. {item.title} — {item.url}\n{item.snippet}")
    return "\n\n".join(lines)


def source_memory(results: list[SearchResult]):
    if not results:
        return ""
    return "Live sources used:\n" + "\n".join(
        f"- {item.title} ({item.domain}) {item.url}" for item in results
    )
