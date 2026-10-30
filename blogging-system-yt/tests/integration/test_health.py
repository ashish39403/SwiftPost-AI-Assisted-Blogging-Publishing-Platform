from django.test import TestCase
from rest_framework.test import APIClient


class HealthApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_health_is_public(self):
        response = self.client.get("/api/v1/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "service": "swiftpost-api"})

    def test_health_rejects_other_methods_with_error_envelope(self):
        response = self.client.post("/api/v1/health/", {}, format="json")

        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json()["error"]["code"], "METHOD_NOT_ALLOWED")

    def test_unknown_api_path_uses_error_envelope(self):
        response = self.client.get("/api/v1/does-not-exist/")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "NOT_FOUND")
        self.assertNotIn("traceback", response.content.decode().lower())

    def test_allowed_frontend_origin_receives_cors_header(self):
        response = self.client.get("/api/v1/health/", HTTP_ORIGIN="http://localhost:3000")

        self.assertEqual(response["Access-Control-Allow-Origin"], "http://localhost:3000")
        self.assertEqual(response["Access-Control-Allow-Credentials"], "true")
