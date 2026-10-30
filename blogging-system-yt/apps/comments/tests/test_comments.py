from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Role, User
from apps.blogs.models import PostStatus
from apps.comments.models import Comment, CommentStatus, PostLike


def user(username, role):
    return User.objects.create_user(
        email=f"{username}@example.com",
        username=username,
        password="a-long-unique-pass-19",
        role=role,
    )


class CommentAndLikeTests(TestCase):
    def setUp(self):
        self.author = user("ada", Role.AUTHOR)
        self.reader = user("reed", Role.READER)
        self.admin = user("admin", Role.ADMIN)
        self.author_client = APIClient()
        self.reader_client = APIClient()
        self.admin_client = APIClient()
        self.public = APIClient()
        self.author_client.force_authenticate(user=self.author)
        self.reader_client.force_authenticate(user=self.reader)
        self.admin_client.force_authenticate(user=self.admin)
        category_id = self.admin_client.post(
            "/api/v1/categories/",
            {"name": "Energy"},
            format="json",
        ).json()["id"]
        self.post_id = self.author_client.post(
            "/api/v1/drafts/",
            {
                "title": "Live solar",
                "excerpt": "A short excerpt",
                "body": "The full story.",
                "category_id": category_id,
            },
            format="json",
        ).json()["id"]
        published = self.author_client.post(f"/api/v1/blogs/{self.post_id}/publish/", {}, format="json")
        self.assertEqual(published.status_code, 200)

    def test_published_post_accepts_likes_and_shows_logged_in_comments(self):
        liked = self.reader_client.post(f"/api/v1/blogs/{self.post_id}/likes/", {}, format="json")
        self.assertEqual(liked.status_code, 200)
        self.assertTrue(liked.json()["liked"])
        self.assertEqual(liked.json()["count"], 1)
        self.assertEqual(PostLike.objects.count(), 1)

        unliked = self.reader_client.post(f"/api/v1/blogs/{self.post_id}/likes/", {}, format="json")
        self.assertFalse(unliked.json()["liked"])
        self.assertEqual(unliked.json()["count"], 0)

        self.reader_client.post(f"/api/v1/blogs/{self.post_id}/likes/", {}, format="json")
        author_comment = self.author_client.post(
            f"/api/v1/blogs/{self.post_id}/comments/",
            {"body": "Thanks for reading."},
            format="json",
        )
        self.assertEqual(author_comment.status_code, 201)
        self.assertEqual(author_comment.json()["status"], CommentStatus.APPROVED)

        reader_comment = self.reader_client.post(
            f"/api/v1/blogs/{self.post_id}/comments/",
            {"body": "I have a question."},
            format="json",
        )
        self.assertEqual(reader_comment.status_code, 201)
        self.assertEqual(reader_comment.json()["status"], CommentStatus.APPROVED)

        public = self.public.get(f"/api/v1/blogs/{self.post_id}/comments/")
        self.assertEqual(public.status_code, 200)
        self.assertEqual(public.json()["count"], 2)
        bodies = {item["body"] for item in public.json()["results"]}
        self.assertEqual(bodies, {"Thanks for reading.", "I have a question."})

        story = self.public.get(f"/api/v1/blogs/{self.post_id}/").json()
        self.assertEqual(story["like_count"], 1)
        self.assertEqual(story["comment_count"], 2)
        self.assertFalse(story["liked"])

        draft = self.author_client.post("/api/v1/drafts/", {"title": "Secret"}, format="json").json()
        hidden = self.reader_client.post(
            f"/api/v1/blogs/{draft['id']}/comments/",
            {"body": "Nope"},
            format="json",
        )
        self.assertEqual(hidden.status_code, 404)
        self.assertEqual(Comment.objects.filter(post_id=draft["id"]).count(), 0)
        self.assertEqual(self.public.post(f"/api/v1/blogs/{self.post_id}/likes/", {}, format="json").status_code, 401)
