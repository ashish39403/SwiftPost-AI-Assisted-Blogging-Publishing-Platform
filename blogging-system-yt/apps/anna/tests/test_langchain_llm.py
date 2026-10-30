import json
from unittest.mock import patch

from django.test import TestCase, override_settings

from apps.anna.interfaces.llm import ChatMessage, GenerationRequest
from apps.anna.orchestration.generation import compose_request, review_request
from apps.anna.providers.selected_llm import OpenAICompatibleLLM
from apps.composer.parsers import parse_article


class FakeChat:
    def __init__(self, content):
        self.content = content
        self.calls = []
        self.bound = []

    def bind(self, **kwargs):
        self.bound.append(kwargs)
        return self

    def invoke(self, messages):
        self.calls.append(messages)
        return type("Result", (), {"content": self.content})()

    def stream(self, messages):
        self.calls.append(messages)
        yield type("Chunk", (), {"content": self.content})()


class LangChainAdapterTests(TestCase):
    def test_prompt_templates_stay_inside_application_message_types(self):
        compose = compose_request("Local solar")
        self.assertEqual(compose.kind, "compose")
        self.assertEqual(compose.messages[0].role, "system")
        self.assertIn("Local solar", compose.messages[1].content)
        self.assertIn("Unable to help", compose.messages[0].content)
        self.assertIn("illegal", compose.messages[0].content)
        self.assertIn("Opening", compose.messages[1].content)

        review = review_request("Title", "Excerpt", "Body")
        self.assertEqual(review.kind, "review")
        self.assertIn("Strengths", review.messages[0].content)
        self.assertIn("Verdict", review.messages[0].content)
        self.assertIn("Do this first", review.messages[0].content)
        self.assertIn("illegal", review.messages[0].content)

    @override_settings(
        AI_PROVIDER_API_KEY="test-key",
        AI_PROVIDER_BASE_URL="https://example.invalid/v1",
        AI_MODEL="gpt-4o-mini",
        AI_MODEL_COMPOSE="",
        AI_MODEL_REVIEW="",
    )
    def test_compose_adapter_normalizes_langchain_json(self):
        fake = FakeChat('```json\n{"title": "A", "excerpt": "B", "body": "C"}\n```')
        with patch("apps.anna.providers.selected_llm._running_django_tests", return_value=False):
            with patch("langchain_openai.ChatOpenAI", return_value=fake):
                result = OpenAICompatibleLLM().generate(
                    GenerationRequest(
                        kind="compose",
                        messages=[ChatMessage(role="user", content="Write it")],
                    )
                )
        article = parse_article(result.text)
        self.assertEqual(article["title"], "A")
        self.assertEqual(article["excerpt"], "B")
        self.assertEqual(article["body"], "C")
        self.assertEqual(result.model, "gpt-4o-mini")
        self.assertEqual(len(fake.calls), 1)

    @override_settings(
        AI_PROVIDER_API_KEY="test-key",
        AI_PROVIDER_BASE_URL="https://example.invalid/v1",
        AI_MODEL="openai/gpt-5.4-mini",
        AI_MODEL_COMPOSE="openai/gpt-5.5",
        AI_MODEL_REVIEW="openai/gpt-5.5",
    )
    def test_compose_and_review_use_separate_models(self):
        fake = FakeChat('{"title": "A", "excerpt": "B", "body": "C"}')
        with patch("apps.anna.providers.selected_llm._running_django_tests", return_value=False):
            with patch("apps.anna.providers.selected_llm._chat_model", return_value=fake) as chat:
                composed = OpenAICompatibleLLM().generate(
                    GenerationRequest(
                        kind="compose",
                        messages=[ChatMessage(role="user", content="Write it")],
                    )
                )
                reviewed = OpenAICompatibleLLM().generate(
                    GenerationRequest(
                        kind="review",
                        messages=[ChatMessage(role="user", content="Check it")],
                    )
                )
        self.assertEqual(composed.model, "openai/gpt-5.5")
        self.assertEqual(reviewed.model, "openai/gpt-5.5")
        self.assertEqual(chat.call_args_list[0].kwargs["model"], "openai/gpt-5.5")
        self.assertEqual(chat.call_args_list[1].kwargs["model"], "openai/gpt-5.5")

    @override_settings(
        AI_PROVIDER_API_KEY="test-key",
        AI_PROVIDER_BASE_URL="https://api.aicredits.in/v1",
        AI_MODEL_COMPOSE="openai/gpt-5.5",
    )
    def test_gpt5_chat_uses_completions_api_without_json_mode(self):
        fake = FakeChat('{"title": "A", "excerpt": "B", "body": "C"}')
        request = GenerationRequest(
            kind="compose",
            messages=[ChatMessage(role="user", content="Write it")],
            max_tokens=4000,
            timeout=180,
        )
        with patch("langchain_openai.ChatOpenAI", return_value=fake) as cls:
            from apps.anna.providers.selected_llm import _chat_model

            _chat_model(
                model="openai/gpt-5.5",
                key="test-key",
                base="https://api.aicredits.in/v1",
                request=request,
            )
        kwargs = cls.call_args.kwargs
        self.assertEqual(kwargs["model"], "openai/gpt-5.5")
        self.assertEqual(kwargs["base_url"], "https://api.aicredits.in/v1")
        self.assertEqual(kwargs["use_responses_api"], False)
        self.assertEqual(kwargs["max_completion_tokens"], 4000)
        self.assertNotIn("temperature", kwargs)
        self.assertEqual(fake.bound, [])
