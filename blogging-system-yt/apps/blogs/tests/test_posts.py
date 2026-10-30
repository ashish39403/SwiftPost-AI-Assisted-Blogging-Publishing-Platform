from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Role, User
from apps.blogs.models import PostStatus
from apps.categories.models import Category
from apps.publishing.models import PublishingEvent


def user(username, role):
    return User.objects.create_user(
        email=f"{username}@example.com",
        username=username,
        password="a-long-unique-pass-19",
        role=role,
    )


class PublishingApiTests(TestCase):
    def setUp(self):
        self.author = user("ada", Role.AUTHOR)
        self.other = user("grace", Role.AUTHOR)
        self.reader = user("reed", Role.READER)
        self.admin = user("admin", Role.ADMIN)
        self.client = APIClient()
        self.author_client = APIClient()
        self.other_client = APIClient()
        self.reader_client = APIClient()
        self.admin_client = APIClient()
        self.author_client.force_authenticate(user=self.author)
        self.other_client.force_authenticate(user=self.other)
        self.reader_client.force_authenticate(user=self.reader)
        self.admin_client.force_authenticate(user=self.admin)

    def test_draft_stays_private_until_the_author_publishes_it(self):
        category = self.admin_client.post(
            "/api/v1/categories/",
            {"name": "Energy", "description": "Power"},
            format="json",
        )
        self.assertEqual(category.status_code, 201)
        category_id = category.json()["id"]

        created = self.author_client.post(
            "/api/v1/drafts/",
            {
                "title": "Clean energy",
                "excerpt": "A short excerpt",
                "body": "The full story.",
                "category_id": category_id,
                "status": "published",
            },
            format="json",
        )
        self.assertEqual(created.status_code, 400)

        created = self.author_client.post(
            "/api/v1/drafts/",
            {
                "title": "Clean energy",
                "excerpt": "A short excerpt",
                "body": "The full story.",
                "category_id": category_id,
            },
            format="json",
        )
        self.assertEqual(created.status_code, 201)
        post_id = created.json()["id"]
        self.assertEqual(created.json()["status"], PostStatus.DRAFT)
        self.assertEqual(created.json()["slug"], "clean-energy")

        self.assertEqual(self.client.get("/api/v1/blogs/").json()["count"], 0)
        self.assertEqual(self.client.get(f"/api/v1/blogs/{post_id}/").status_code, 404)
        self.assertEqual(
            self.client.get(f"/api/v1/blogs/{post_id}/").json()["error"]["code"],
            "POST_NOT_FOUND",
        )
        self.assertEqual(self.other_client.get(f"/api/v1/drafts/{post_id}/").status_code, 404)
        self.assertEqual(self.reader_client.post("/api/v1/drafts/", {}, format="json").status_code, 403)

        blocked = self.other_client.post(f"/api/v1/blogs/{post_id}/publish/", {}, format="json")
        self.assertEqual(blocked.status_code, 404)
        self.assertEqual(self.client.get("/api/v1/blogs/").json()["count"], 0)

        published = self.author_client.post(f"/api/v1/blogs/{post_id}/publish/", {}, format="json")
        self.assertEqual(published.status_code, 200)
        self.assertEqual(published.json()["status"], PostStatus.PUBLISHED)
        self.assertIsNotNone(published.json()["published_at"])
        self.assertEqual(PublishingEvent.objects.filter(post_id=post_id).count(), 1)

        taken_down = self.admin_client.post(f"/api/v1/blogs/{post_id}/unpublish/", {}, format="json")
        self.assertEqual(taken_down.status_code, 200)
        self.assertEqual(self.client.get("/api/v1/blogs/").json()["count"], 0)
        republished = self.author_client.post(f"/api/v1/blogs/{post_id}/publish/", {}, format="json")
        self.assertEqual(republished.status_code, 200)

        public = self.client.get("/api/v1/blogs/?search=clean&category=energy")
        self.assertEqual(public.status_code, 200)
        self.assertEqual(public.json()["count"], 1)
        self.assertEqual(public.json()["results"][0]["author"], {"id": self.author.id, "username": "ada"})
        self.assertNotIn("email", public.json()["results"][0]["author"])

    def test_incomplete_draft_cannot_be_published(self):
        created = self.author_client.post("/api/v1/drafts/", {"title": "Notes"}, format="json")
        response = self.author_client.post(
            f"/api/v1/blogs/{created.json()['id']}/publish/",
            {},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "VALIDATION_ERROR")
        self.assertIn("body", response.json()["error"]["details"])

    def test_author_cannot_edit_or_delete_another_authors_post(self):
        created = self.author_client.post(
            "/api/v1/drafts/",
            {"title": "Mine", "excerpt": "Mine", "body": "Mine"},
            format="json",
        )
        post_id = created.json()["id"]
        self.assertEqual(
            self.other_client.patch(
                f"/api/v1/drafts/{post_id}/",
                {"title": "Stolen"},
                format="json",
            ).status_code,
            404,
        )
        self.assertEqual(self.other_client.delete(f"/api/v1/drafts/{post_id}/").status_code, 404)

    def test_published_post_is_locked_and_archive_removes_it_from_public(self):
        category_id = self.admin_client.post(
            "/api/v1/categories/",
            {"name": "Cities"},
            format="json",
        ).json()["id"]
        post_id = self.author_client.post(
            "/api/v1/drafts/",
            {
                "title": "Copenhagen",
                "excerpt": "A city",
                "body": "A longer body.",
                "category_id": category_id,
            },
            format="json",
        ).json()["id"]
        published = self.author_client.post(f"/api/v1/blogs/{post_id}/publish/", {}, format="json")
        self.assertEqual(published.status_code, 200)

        locked = self.author_client.patch(
            f"/api/v1/drafts/{post_id}/",
            {"title": "Changed"},
            format="json",
        )
        self.assertEqual(locked.status_code, 400)

        archived = self.admin_client.post(f"/api/v1/blogs/{post_id}/archive/", {}, format="json")
        self.assertEqual(archived.status_code, 400)
        self.assertEqual(archived.json()["error"]["code"], "INVALID_TRANSITION")

        self.admin_client.post(f"/api/v1/blogs/{post_id}/unpublish/", {}, format="json")
        archived = self.admin_client.post(f"/api/v1/blogs/{post_id}/archive/", {}, format="json")
        self.assertEqual(archived.status_code, 200)
        self.assertEqual(self.client.get("/api/v1/blogs/").json()["count"], 0)
        self.assertEqual(self.author_client.get("/api/v1/drafts/").json()["count"], 0)

    def test_anonymous_draft_create_requires_authentication(self):
        response = self.client.post("/api/v1/drafts/", {"title": "Nope"}, format="json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "AUTHENTICATION_REQUIRED")

    def test_public_list_paginates_published_posts_only(self):
        category_id = self.admin_client.post(
            "/api/v1/categories/",
            {"name": "Grid"},
            format="json",
        ).json()["id"]
        for number in range(11):
            post_id = self.author_client.post(
                "/api/v1/drafts/",
                {
                    "title": f"Story {number}",
                    "excerpt": "Excerpt",
                    "body": "Body",
                    "category_id": category_id,
                },
                format="json",
            ).json()["id"]
            self.author_client.post(f"/api/v1/blogs/{post_id}/publish/", {}, format="json")
        self.author_client.post("/api/v1/drafts/", {"title": "Still private"}, format="json")

        first = self.client.get("/api/v1/blogs/?page_size=10")
        second = self.client.get("/api/v1/blogs/?page=2&page_size=10")
        self.assertEqual(first.json()["count"], 11)
        self.assertEqual(len(first.json()["results"]), 10)
        self.assertEqual(len(second.json()["results"]), 1)

    def test_inactive_category_is_hidden_and_cannot_be_used_for_a_new_draft(self):
        created = self.admin_client.post("/api/v1/categories/", {"name": "Old"}, format="json")
        category_id = created.json()["id"]
        removed = self.admin_client.delete(f"/api/v1/categories/{category_id}/")
        self.assertEqual(removed.status_code, 200)
        self.assertFalse(removed.json()["is_active"])
        public_categories = self.client.get("/api/v1/categories/").json()["results"]
        self.assertNotIn("archive", [item["slug"] for item in public_categories])
        self.assertEqual(self.client.get(f"/api/v1/categories/{category_id}/").status_code, 404)
        self.assertFalse(Category.objects.get(pk=category_id).is_active)

        rejected = self.author_client.post(
            "/api/v1/drafts/",
            {"title": "Nope", "category_id": category_id},
            format="json",
        )
        self.assertEqual(rejected.status_code, 400)
        self.assertEqual(self.reader_client.post("/api/v1/categories/", {"name": "Nope"}, format="json").status_code, 403)
