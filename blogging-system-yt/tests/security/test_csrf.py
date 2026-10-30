import json

from django.test import Client, TestCase


class CsrfSecurityTests(TestCase):
    def test_login_without_csrf_token_is_rejected_when_checks_are_enforced(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(
            "/api/v1/auth/login/",
            data=json.dumps(
                {"email": "ada@example.com", "password": "a-long-unique-pass-19"}
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "CSRF_FAILED")

    def test_anonymous_draft_create_without_csrf_asks_for_authentication(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(
            "/api/v1/drafts/",
            data=json.dumps({"title": "Nope"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "AUTHENTICATION_REQUIRED")

    def test_csrf_endpoint_lets_the_same_client_log_in(self):
        client = Client(enforce_csrf_checks=True)
        token = client.get("/api/v1/auth/csrf/").json()["csrfToken"]
        registered = client.post(
            "/api/v1/auth/register/",
            data=json.dumps(
                {
                    "username": "ada",
                    "email": "ada@example.com",
                    "password": "a-long-unique-pass-19",
                }
            ),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(registered.status_code, 201)

        response = client.post(
            "/api/v1/auth/login/",
            data=json.dumps(
                {"email": "ada@example.com", "password": "a-long-unique-pass-19"}
            ),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["role"], "author")
