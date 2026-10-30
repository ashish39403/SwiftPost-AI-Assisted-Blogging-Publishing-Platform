from django.conf import settings

from apps.anna.exceptions import ProviderNotConfigured
from apps.anna.providers.selected_llm import OpenAICompatibleLLM
from apps.anna.providers.tavily import TavilySearchProvider


def get_search_provider():
    name = settings.SEARCH_PROVIDER or ("tavily" if settings.TAVILY_API_KEY else "")
    if name == "tavily":
        return TavilySearchProvider()
    raise ProviderNotConfigured("Search is not configured.")


def get_llm_provider():
    if settings.AI_PROVIDER_API_KEY and settings.AI_PROVIDER_BASE_URL:
        return OpenAICompatibleLLM()
    raise ProviderNotConfigured("The writing model is not configured.")
