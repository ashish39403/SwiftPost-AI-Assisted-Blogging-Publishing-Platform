from django.test import SimpleTestCase, override_settings

from apps.anna.providers.model_config import (
    DEFAULT_COMPOSE,
    DEFAULT_REVIEW,
    chat_options,
    clean_model_id,
    is_reasoning_model,
    model_for_kind,
)
from apps.anna.providers.selected_llm import model_for


class ModelConfigTests(SimpleTestCase):
    def test_clean_model_id_strips_quotes_and_spaces(self):
        self.assertEqual(clean_model_id('  "openai/gpt-5.5"  '), "openai/gpt-5.5")

    def test_task_models_prefer_compose_and_review(self):
        self.assertEqual(
            model_for_kind("compose", compose="openai/gpt-5.5", review="x", fallback="openai/gpt-5.4-mini"),
            "openai/gpt-5.5",
        )
        self.assertEqual(
            model_for_kind("review", compose="x", review="openai/gpt-5.5", fallback="openai/gpt-5.4-mini"),
            "openai/gpt-5.5",
        )
        self.assertEqual(
            model_for_kind("compose", compose="", review="", fallback=""),
            "nvidia/nemotron-3-super-120b-a12b",
        )

    def test_gpt5_is_reasoning_and_skips_temperature(self):
        self.assertTrue(is_reasoning_model("openai/gpt-5.5"))
        options = chat_options("compose", "openai/gpt-5.5", max_tokens=4000, timeout=180)
        self.assertEqual(options["model"], "openai/gpt-5.5")
        self.assertEqual(options["use_responses_api"], False)
        self.assertEqual(options["max_completion_tokens"], 4000)
        self.assertNotIn("temperature", options)

    def test_gpt4o_mini_keeps_temperature(self):
        self.assertFalse(is_reasoning_model("gpt-4o-mini"))
        options = chat_options("review", "gpt-4o-mini", max_tokens=1800, timeout=90)
        self.assertEqual(options["temperature"], 0.25)
        self.assertEqual(options["max_completion_tokens"], 1800)

    @override_settings(AI_MODEL="openai/gpt-5.4-mini", AI_MODEL_COMPOSE="openai/gpt-5.5", AI_MODEL_REVIEW="openai/gpt-5.5")
    def test_selected_models_match_env_task_ids(self):
        self.assertEqual(model_for("compose"), "openai/gpt-5.5")
        self.assertEqual(model_for("review"), "openai/gpt-5.5")
        self.assertEqual(model_for("other"), "openai/gpt-5.4-mini")
        self.assertEqual(DEFAULT_COMPOSE, "nvidia/nemotron-3-super-120b-a12b")
        self.assertEqual(DEFAULT_REVIEW, "openai/gpt-5.5")
