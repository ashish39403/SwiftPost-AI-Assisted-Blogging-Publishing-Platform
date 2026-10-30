from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Role, User
from apps.anna.interfaces.llm import ProviderGenerationResult
from apps.blogs.models import PostStatus


def user(username, role):
    return User.objects.create_user(
        email=f"{username}@example.com",
        username=username,
        password="a-long-unique-pass-19",
        role=role,
    )


class FakeLLM:
    def generate(self, request):
        return ProviderGenerationResult(
            text="Strengths\nClear title.\n\nGaps\nNeeds a local example.\n\nSuggested edits\nTighten the opening.",
            model="fake-anna",
        )


class AnnaReviewTests(TestCase):
    def setUp(self):
        self.author = user("ada", Role.AUTHOR)
        self.other = user("grace", Role.AUTHOR)
        self.author_client = APIClient()
        self.other_client = APIClient()
        self.author_client.force_authenticate(user=self.author)
        self.other_client.force_authenticate(user=self.other)
        self.post_id = self.author_client.post(
            "/api/v1/drafts/",
            {"title": "Local power", "excerpt": "A short excerpt", "body": "The full story."},
            format="json",
        ).json()["id"]

    def test_author_can_ask_anna_to_review_an_owned_draft_without_publishing(self):
        with patch("apps.anna.services.get_llm_provider", return_value=FakeLLM()):
            response = self.author_client.post(
                "/api/v1/ai/reviews/",
                {"post_id": self.post_id},
                format="json",
            )
        self.assertEqual(response.status_code, 201)
        self.assertIn("Strengths", response.json()["notes"])
        draft = self.author_client.get(f"/api/v1/drafts/{self.post_id}/").json()
        self.assertEqual(draft["status"], PostStatus.DRAFT)
        self.assertEqual(
            self.other_client.post("/api/v1/ai/reviews/", {"post_id": self.post_id}, format="json").status_code,
            404,
        )

    def test_author_can_resume_private_anna_review_history_without_changing_post_state(self):
        created = self.author_client.post(
            "/api/v1/ai/anna/conversations/",
            {"post_id": self.post_id},
            format="json",
        )
        self.assertEqual(created.status_code, 201)
        conversation_id = created.json()["id"]
        with patch("apps.anna.services.get_llm_provider", return_value=FakeLLM()):
            replied = self.author_client.post(
                f"/api/v1/ai/anna/conversations/{conversation_id}/messages/",
                {"content": "Review the opening for clarity."},
                format="json",
            )
        self.assertEqual(replied.status_code, 200)
        self.assertEqual(len(replied.json()["conversation"]["messages"]), 2)
        self.assertEqual(self.other_client.get(f"/api/v1/ai/anna/conversations/{conversation_id}/").status_code, 404)
        draft = self.author_client.get(f"/api/v1/drafts/{self.post_id}/").json()
        self.assertEqual(draft["status"], PostStatus.DRAFT)
        archived = self.author_client.post(f"/api/v1/ai/anna/conversations/{conversation_id}/archive/", {}, format="json")
        self.assertEqual(archived.status_code, 200)
        self.assertEqual(self.author_client.get("/api/v1/ai/anna/conversations/").json()["count"], 0)
        assistant_message_id = replied.json()["conversation"]["messages"][1]["id"]
        handoff = self.author_client.post(
            f"/api/v1/ai/anna/messages/{assistant_message_id}/continue-in-composer/", {}, format="json"
        )
        self.assertEqual(handoff.status_code, 201)
        self.assertEqual(handoff.json()["messages"][0]["content"], replied.json()["conversation"]["messages"][1]["content"])
