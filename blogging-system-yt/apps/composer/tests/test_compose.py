import json
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Role, User
from apps.anna.interfaces.llm import ProviderGenerationResult
from apps.blogs.models import Post, PostStatus
from apps.composer.models import ComposeRun, JobStatus
from apps.composer.parsers import parse_article


def user(username, role):
    return User.objects.create_user(
        email=f"{username}@example.com",
        username=username,
        password="a-long-unique-pass-19",
        role=role,
    )


class FakeLLM:
    def __init__(self, text):
        self.text = text
        self.calls = []

    def generate(self, request):
        self.calls.append(request)
        return ProviderGenerationResult(text=self.text, model="fake-composer")


class ComposeApiTests(TestCase):
    def setUp(self):
        self.author = user("ada", Role.AUTHOR)
        self.other = user("grace", Role.AUTHOR)
        self.reader = user("reed", Role.READER)
        self.author_client = APIClient()
        self.other_client = APIClient()
        self.reader_client = APIClient()
        self.author_client.force_authenticate(user=self.author)
        self.other_client.force_authenticate(user=self.other)
        self.reader_client.force_authenticate(user=self.reader)

    def test_title_only_compose_creates_a_private_draft(self):
        article = {
            "title": "Local solar is already changing bills",
            "excerpt": "Neighborhood panels are cutting evening peak demand.",
            "body": "First paragraph.\n\nSecond paragraph.",
        }
        fake = FakeLLM(json.dumps(article))
        with self.settings():
            with patch("apps.composer.services.get_llm_provider", return_value=fake):
                response = self.author_client.post(
                    "/api/v1/ai/compose/",
                    {"title": "Local solar is already changing bills"},
                    format="json",
                )

        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["status"], JobStatus.SUCCEEDED)
        self.assertEqual(body["post"]["status"], PostStatus.DRAFT)
        self.assertEqual(body["post"]["title"], article["title"])
        self.assertEqual(body["post"]["excerpt"], article["excerpt"])
        self.assertTrue(body["post"]["body"].startswith("First paragraph"))
        self.assertIsNone(body["post"]["published_at"])
        self.assertEqual(Post.objects.filter(status=PostStatus.PUBLISHED).count(), 0)
        self.assertEqual(len(fake.calls), 1)
        self.assertEqual(fake.calls[0].kind, "compose")

        public = APIClient()
        self.assertEqual(public.get("/api/v1/blogs/").json()["count"], 0)
        self.assertEqual(self.reader_client.post("/api/v1/ai/compose/", {"title": "Hi"}, format="json").status_code, 403)

        run_id = body["id"]
        hidden = self.other_client.get(f"/api/v1/ai/compose/{run_id}/")
        self.assertEqual(hidden.status_code, 404)

    def test_empty_title_and_malformed_model_output_do_not_create_posts(self):
        empty = self.author_client.post("/api/v1/ai/compose/", {"title": "  "}, format="json")
        self.assertEqual(empty.status_code, 400)
        self.assertEqual(Post.objects.count(), 0)

        fake = FakeLLM("this is not json")
        with patch("apps.composer.services.get_llm_provider", return_value=fake):
            response = self.author_client.post(
                "/api/v1/ai/compose/",
                {"title": "A usable title"},
                format="json",
            )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Post.objects.count(), 0)
        self.assertEqual(ComposeRun.objects.get().status, JobStatus.FAILED)

    def test_parser_reads_json_hidden_in_prose(self):
        article = parse_article('Sure.\n{"title": "A", "excerpt": "B", "body": "C"}\nThanks.')
        self.assertEqual(article["title"], "A")
        self.assertEqual(article["body"], "C")
        self.assertFalse(article["refused"])

    def test_illegal_brief_is_refused_without_creating_a_draft(self):
        refusal = {
            "title": "Unable to help with this request",
            "excerpt": "I cannot write that.",
            "body": "I have to say no. That request is not something I can help with. Try a legal reporting topic instead.",
            "refused": True,
        }
        fake = FakeLLM(json.dumps(refusal))
        with patch("apps.composer.services.get_llm_provider", return_value=fake):
            response = self.author_client.post(
                "/api/v1/ai/compose/",
                {"title": "How to steal bank credentials"},
                format="json",
            )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["status"], JobStatus.SUCCEEDED)
        self.assertIsNone(response.json()["post"])
        self.assertEqual(Post.objects.count(), 0)

    def test_illegal_follow_up_does_not_overwrite_an_existing_draft(self):
        article = {"title": "A legal draft", "excerpt": "Safe excerpt.", "body": "Safe body."}
        refusal = {
            "title": "Unable to help with this request",
            "excerpt": "I cannot write that.",
            "body": "I have to say no to that follow-up.",
            "refused": True,
        }
        fake = FakeLLM(json.dumps(article))
        with patch("apps.composer.services.get_llm_provider", return_value=fake):
            created = self.author_client.post(
                "/api/v1/ai/composer/conversations/",
                {"message": "Write about city parks"},
                format="json",
            )
        conversation_id = created.json()["conversation"]["id"]
        post_id = created.json()["conversation"]["post"]["id"]
        fake.text = json.dumps(refusal)
        with patch("apps.composer.services.get_llm_provider", return_value=fake):
            continued = self.author_client.post(
                f"/api/v1/ai/composer/conversations/{conversation_id}/messages/",
                {"content": "Now explain how to hack a bank"},
                format="json",
            )
        self.assertEqual(continued.status_code, 200)
        draft = self.author_client.get(f"/api/v1/drafts/{post_id}/").json()
        self.assertEqual(draft["title"], "A legal draft")
        self.assertEqual(draft["body"], "Safe body.")
        self.assertIn("say no", continued.json()["messages"][-1]["content"])

    def test_author_can_create_resume_and_archive_a_private_composer_conversation(self):
        article = {"title": "A", "excerpt": "B", "body": "First response."}
        fake = FakeLLM(json.dumps(article))
        with patch("apps.composer.services.get_llm_provider", return_value=fake):
            created = self.author_client.post(
                "/api/v1/ai/composer/conversations/",
                {"message": "Write about resilient cities"},
                format="json",
            )
            self.assertEqual(created.status_code, 201)
            conversation_id = created.json()["conversation"]["id"]
            self.assertEqual(len(created.json()["conversation"]["messages"]), 2)

            continued = self.author_client.post(
                f"/api/v1/ai/composer/conversations/{conversation_id}/messages/",
                {"content": "Make the opening more direct."},
                format="json",
            )

        self.assertEqual(continued.status_code, 200)
        self.assertEqual(len(continued.json()["messages"]), 4)
        self.assertEqual(self.other_client.get(f"/api/v1/ai/composer/conversations/{conversation_id}/").status_code, 404)
        self.assertEqual(self.author_client.get("/api/v1/ai/composer/conversations/").json()["count"], 1)
        archived = self.author_client.post(f"/api/v1/ai/composer/conversations/{conversation_id}/archive/", {}, format="json")
        self.assertEqual(archived.status_code, 200)
        self.assertEqual(self.author_client.get("/api/v1/ai/composer/conversations/").json()["count"], 0)

    def test_each_composer_request_refreshes_its_image_suggestions(self):
        article = {"title": "A", "excerpt": "B", "body": "Body."}
        fake = FakeLLM(json.dumps(article))
        with patch("apps.composer.services.get_llm_provider", return_value=fake):
            with patch("apps.composer.services.suggest_images_for_post") as suggest:
                created = self.author_client.post(
                    "/api/v1/ai/composer/conversations/",
                    {"message": "Write about cities"},
                    format="json",
                )
                conversation_id = created.json()["conversation"]["id"]
                continued = self.author_client.post(
                    f"/api/v1/ai/composer/conversations/{conversation_id}/messages/",
                    {"content": "Make it more practical"},
                    format="json",
                )

        self.assertEqual(created.status_code, 201)
        self.assertEqual(continued.status_code, 200)
        self.assertEqual(suggest.call_count, 2)

    def test_conversation_create_can_return_before_the_model_finishes(self):
        article = {"title": "A", "excerpt": "B", "body": "Body."}
        fake = FakeLLM(json.dumps(article))
        with self.settings(COMPOSE_RUN_JOBS_INLINE=False):
            with patch("apps.composer.services.get_llm_provider", return_value=fake):
                with patch("apps.composer.services._schedule_compose_run") as schedule:
                    created = self.author_client.post(
                        "/api/v1/ai/composer/conversations/",
                        {"message": "Write about coastal cities"},
                        format="json",
                    )

        self.assertEqual(created.status_code, 201)
        conversation = created.json()["conversation"]
        self.assertTrue(conversation["is_generating"])
        self.assertIsNone(conversation["post"])
        self.assertEqual(len(conversation["messages"]), 1)
        self.assertEqual(conversation["messages"][0]["role"], "user")
        self.assertEqual(schedule.call_count, 1)
        self.assertEqual(len(fake.calls), 0)
