import tempfile
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.test import APIClient

from apps.accounts.models import Role, User
from apps.media_assets.models import MediaAsset
from apps.media_assets.storage import S3Storage


def user(username, role):
    return User.objects.create_user(
        email=f"{username}@example.com",
        username=username,
        password="a-long-unique-pass-19",
        role=role,
    )


def image_file(name="photo.png", fmt="PNG", size=(12, 8), content_type="image/png"):
    from io import BytesIO

    buffer = BytesIO()
    Image.new("RGB", size, "red").save(buffer, format=fmt)
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=content_type)


class FeaturedImageTests(TestCase):
    def setUp(self):
        self.media = tempfile.TemporaryDirectory()
        self.settings = override_settings(MEDIA_ROOT=self.media.name)
        self.settings.enable()
        self.author = user("ada", Role.AUTHOR)
        self.other = user("grace", Role.AUTHOR)
        self.reader = user("reed", Role.READER)
        self.author_client = APIClient()
        self.other_client = APIClient()
        self.reader_client = APIClient()
        self.public = APIClient()
        self.author_client.force_authenticate(user=self.author)
        self.other_client.force_authenticate(user=self.other)
        self.reader_client.force_authenticate(user=self.reader)
        self.post_id = self.author_client.post(
            "/api/v1/drafts/",
            {"title": "With a photo"},
            format="json",
        ).json()["id"]

    def tearDown(self):
        self.settings.disable()
        self.media.cleanup()

    def test_author_attaches_a_featured_image_without_storing_bytes_in_the_row(self):
        response = self.author_client.post(
            "/api/v1/media/upload/",
            {"post_id": self.post_id, "file": image_file(name="../../trip/photo.png")},
            format="multipart",
        )

        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["original_filename"], "photo.png")
        self.assertEqual(body["content_type"], "image/png")
        self.assertEqual(body["width"], 12)
        self.assertEqual(body["height"], 8)
        self.assertTrue(body["url"].startswith("/media/uploads/"))
        self.assertNotIn("..", body["url"])
        self.assertNotIn("://", body["url"])

        asset = MediaAsset.objects.get(pk=body["id"])
        self.assertTrue(asset.storage_key.startswith("uploads/"))
        self.assertTrue(asset.storage_key.endswith(".png"))
        self.assertNotIn("photo", asset.storage_key)
        stored = Path(self.media.name, asset.storage_key)
        self.assertTrue(stored.exists())
        self.assertGreater(stored.stat().st_size, 0)

        draft = self.author_client.get(f"/api/v1/drafts/{self.post_id}/").json()
        self.assertEqual(draft["featured_image"]["id"], asset.id)
        self.assertEqual(self.public.get(f"/api/v1/media/{asset.id}/").status_code, 404)

    def test_invalid_and_unauthorized_uploads_are_rejected(self):
        fake = SimpleUploadedFile("notes.png", b"not-an-image", content_type="image/png")
        rejected = self.author_client.post(
            "/api/v1/media/upload/",
            {"post_id": self.post_id, "file": fake},
            format="multipart",
        )
        self.assertEqual(rejected.status_code, 400)
        self.assertEqual(rejected.json()["error"]["code"], "VALIDATION_ERROR")

        mismatched = image_file(name="photo.jpg", content_type="image/png")
        self.assertEqual(
            self.author_client.post(
                "/api/v1/media/upload/",
                {"post_id": self.post_id, "file": mismatched},
                format="multipart",
            ).status_code,
            400,
        )
        self.assertEqual(
            self.reader_client.post(
                "/api/v1/media/upload/",
                {"post_id": self.post_id, "file": image_file()},
                format="multipart",
            ).status_code,
            404,
        )
        self.assertEqual(
            self.other_client.post(
                "/api/v1/media/upload/",
                {"post_id": self.post_id, "file": image_file()},
                format="multipart",
            ).status_code,
            404,
        )
        self.assertFalse(MediaAsset.objects.exists())

    def test_replacement_removes_the_previous_file_and_delete_clears_it(self):
        first = self.author_client.post(
            "/api/v1/media/upload/",
            {"post_id": self.post_id, "file": image_file()},
            format="multipart",
        ).json()
        first_path = Path(self.media.name, MediaAsset.objects.get(pk=first["id"]).storage_key)
        second = self.author_client.post(
            "/api/v1/media/upload/",
            {"post_id": self.post_id, "file": image_file(name="next.png")},
            format="multipart",
        )
        self.assertEqual(second.status_code, 201)
        self.assertFalse(first_path.exists())
        self.assertEqual(MediaAsset.objects.count(), 1)

        deleted = self.author_client.delete(f"/api/v1/media/{second.json()['id']}/")
        self.assertEqual(deleted.status_code, 200)
        self.assertFalse(MediaAsset.objects.exists())
        self.assertIsNone(self.author_client.get(f"/api/v1/drafts/{self.post_id}/").json()["featured_image"])

    def test_s3_adapter_uses_the_server_key_and_public_base_url(self):
        class FakeClient:
            def __init__(self):
                self.calls = []

            def put_object(self, **kwargs):
                self.calls.append(kwargs)

            def delete_object(self, **kwargs):
                self.calls.append(kwargs)

        client = FakeClient()
        storage = S3Storage(client, "bucket", "https://cdn.example.com/media")
        storage.save("uploads/abc.png", b"data", "image/png")
        storage.delete("uploads/abc.png")

        self.assertEqual(storage.url("uploads/abc.png"), "https://cdn.example.com/media/uploads/abc.png")
        self.assertEqual(client.calls[0]["Key"], "uploads/abc.png")
        self.assertEqual(client.calls[0]["ContentType"], "image/png")
        self.assertNotIn("filename", client.calls[0])

    def test_live_image_suggestions_can_be_attached_and_private_urls_are_rejected(self):
        from unittest.mock import patch

        from apps.anna.interfaces.search import ImageResult
        from apps.media_assets.models import ImageSuggestion

        hits = [
            ImageResult(
                url="https://cdn.example.com/solar.jpg",
                description="Rooftop solar",
                page_url="https://example.com/solar",
            )
        ]
        with patch("apps.media_assets.image_search.collect_images", return_value=hits):
            searched = self.author_client.post(
                "/api/v1/media/search-images/",
                {"post_id": self.post_id, "query": "solar panels"},
                format="json",
            )
        self.assertEqual(searched.status_code, 200)
        self.assertEqual(searched.json()[0]["description"], "Rooftop solar")
        suggestion_id = searched.json()[0]["id"]

        png = image_file().read()
        class FakeResponse:
            status_code = 200
            content = png
            headers = {"content-type": "image/png"}

        with patch("apps.media_assets.fetch.public_http_url", side_effect=lambda url: url):
            with patch("apps.media_assets.fetch.httpx.get", return_value=FakeResponse()):
                attached = self.author_client.post(
                    f"/api/v1/media/suggestions/{suggestion_id}/attach/",
                    {},
                    format="json",
                )
        self.assertEqual(attached.status_code, 201)
        self.assertTrue(attached.json()["url"].startswith("/media/uploads/"))
        draft = self.author_client.get(f"/api/v1/drafts/{self.post_id}/").json()
        self.assertEqual(draft["featured_image"]["id"], attached.json()["id"])

        ImageSuggestion.objects.create(
            post_id=self.post_id,
            author=self.author,
            image_url="http://127.0.0.1/secret.png",
        )
        blocked = ImageSuggestion.objects.filter(image_url="http://127.0.0.1/secret.png").get()
        rejected = self.author_client.post(
            f"/api/v1/media/suggestions/{blocked.id}/attach/",
            {},
            format="json",
        )
        self.assertEqual(rejected.status_code, 400)
        self.assertEqual(
            self.other_client.post(
                "/api/v1/media/search-images/",
                {"post_id": self.post_id},
                format="json",
            ).status_code,
            404,
        )

    def test_author_can_save_two_suggested_images_to_one_draft(self):
        from unittest.mock import patch

        from apps.media_assets.models import ImageSuggestion

        first = ImageSuggestion.objects.create(
            post_id=self.post_id,
            author=self.author,
            image_url="https://cdn.example.com/first.png",
        )
        second = ImageSuggestion.objects.create(
            post_id=self.post_id,
            author=self.author,
            image_url="https://cdn.example.com/second.png",
        )
        png = image_file().read()

        class FakeResponse:
            status_code = 200
            content = png
            headers = {"content-type": "image/png"}

        with patch("apps.media_assets.fetch.public_http_url", side_effect=lambda url: url):
            with patch("apps.media_assets.fetch.httpx.get", return_value=FakeResponse()):
                saved = self.author_client.post(
                    "/api/v1/media/suggestions/save/",
                    {"ids": [first.id, second.id]},
                    format="json",
                )

        self.assertEqual(saved.status_code, 200)
        self.assertEqual(len(saved.json()["images"]), 2)
        self.assertEqual(MediaAsset.objects.filter(post_id=self.post_id).count(), 2)
        draft = self.author_client.get(f"/api/v1/drafts/{self.post_id}/").json()
        self.assertEqual(len(draft["images"]), 2)
        self.assertTrue(draft["featured_image"])
        self.assertEqual(ImageSuggestion.objects.filter(post_id=self.post_id, selected=True).count(), 2)

    def test_author_can_save_three_suggested_images_to_one_draft(self):
        from unittest.mock import patch

        from apps.media_assets.models import ImageSuggestion

        suggestions = [
            ImageSuggestion.objects.create(
                post_id=self.post_id,
                author=self.author,
                image_url=f"https://cdn.example.com/{name}.png",
            )
            for name in ("first", "second", "third")
        ]
        png = image_file().read()

        class FakeResponse:
            status_code = 200
            content = png
            headers = {"content-type": "image/png"}

        with patch("apps.media_assets.fetch.public_http_url", side_effect=lambda url: url):
            with patch("apps.media_assets.fetch.httpx.get", return_value=FakeResponse()):
                saved = self.author_client.post(
                    "/api/v1/media/suggestions/save/",
                    {"ids": [item.id for item in suggestions]},
                    format="json",
                )

        self.assertEqual(saved.status_code, 200)
        self.assertEqual(len(saved.json()["images"]), 3)
        draft = self.author_client.get(f"/api/v1/drafts/{self.post_id}/").json()
        self.assertEqual(len(draft["images"]), 3)
        self.assertTrue(draft["featured_image"])
