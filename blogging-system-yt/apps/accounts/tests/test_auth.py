from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Role, User


class AccountApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_stores_username_and_lowercased_email_as_author(self):
        response = self.client.post(
            "/api/v1/auth/register/",
            {
                "username": "Ada",
                "email": "Ada@Example.com",
                "password": "a-long-unique-pass-19",
                "first_name": "Ada",
                "last_name": "Lovelace",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        user = response.json()["user"]
        self.assertEqual(user["username"], "Ada")
        self.assertEqual(user["email"], "ada@example.com")
        self.assertEqual(user["first_name"], "Ada")
        self.assertEqual(user["last_name"], "Lovelace")
        self.assertEqual(user["role"], Role.AUTHOR)
        self.assertNotIn("password", response.json())
        self.assertNotIn("sessionid", response.cookies)

    def test_register_rejects_role_and_staff_fields(self):
        response = self.client.post(
            "/api/v1/auth/register/",
            {
                "username": "ada",
                "email": "ada@example.com",
                "password": "a-long-unique-pass-19",
                "role": "admin",
                "is_staff": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "VALIDATION_ERROR")
        self.assertIn("role", response.json()["error"]["details"])
        self.assertFalse(User.objects.filter(email="ada@example.com").exists())

    def test_duplicate_email_is_rejected_regardless_of_case(self):
        payload = {
            "username": "ada",
            "email": "ada@example.com",
            "password": "a-long-unique-pass-19",
        }
        self.client.post("/api/v1/auth/register/", payload, format="json")
        response = self.client.post(
            "/api/v1/auth/register/",
            {**payload, "username": "ada2", "email": "ADA@example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.json()["error"]["details"])

    def test_login_uses_email_and_rejects_username(self):
        self.client.post(
            "/api/v1/auth/register/",
            {
                "username": "ada",
                "email": "ada@example.com",
                "password": "a-long-unique-pass-19",
            },
            format="json",
        )

        by_username = self.client.post(
            "/api/v1/auth/login/",
            {"username": "ada", "password": "a-long-unique-pass-19"},
            format="json",
        )
        self.assertEqual(by_username.status_code, 400)

        logged_in = APIClient()
        response = logged_in.post(
            "/api/v1/auth/login/",
            {"email": "Ada@Example.com", "password": "a-long-unique-pass-19"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["email"], "ada@example.com")
        me = logged_in.get("/api/v1/auth/me/")
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["user"]["username"], "ada")

    def test_login_failure_does_not_reveal_which_field_was_wrong(self):
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": "missing@example.com", "password": "a-long-unique-pass-19"},
            format="json",
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "AUTHENTICATION_FAILED")
        self.assertEqual(response.json()["error"]["details"], {})

    def test_me_and_logout_require_a_session(self):
        anonymous = self.client.get("/api/v1/auth/me/")
        self.assertEqual(anonymous.status_code, 401)
        self.assertEqual(anonymous.json()["error"]["code"], "AUTHENTICATION_REQUIRED")

        self.client.post(
            "/api/v1/auth/register/",
            {
                "username": "ada",
                "email": "ada@example.com",
                "password": "a-long-unique-pass-19",
            },
            format="json",
        )
        session = APIClient()
        session.post(
            "/api/v1/auth/login/",
            {"email": "ada@example.com", "password": "a-long-unique-pass-19"},
            format="json",
        )
        self.assertEqual(session.post("/api/v1/auth/logout/", {}, format="json").status_code, 200)
        self.assertEqual(session.get("/api/v1/auth/me/").status_code, 401)

    def test_password_change_keeps_the_account_and_replaces_the_password(self):
        self.client.post(
            "/api/v1/auth/register/",
            {
                "username": "ada",
                "email": "ada@example.com",
                "password": "a-long-unique-pass-19",
            },
            format="json",
        )
        session = APIClient()
        session.post(
            "/api/v1/auth/login/",
            {"email": "ada@example.com", "password": "a-long-unique-pass-19"},
            format="json",
        )
        changed = session.post(
            "/api/v1/auth/password/change/",
            {
                "current_password": "a-long-unique-pass-19",
                "new_password": "another-unique-pass-28",
            },
            format="json",
        )
        self.assertEqual(changed.status_code, 200)

        old_login = APIClient()
        self.assertEqual(
            old_login.post(
                "/api/v1/auth/login/",
                {"email": "ada@example.com", "password": "a-long-unique-pass-19"},
                format="json",
            ).status_code,
            401,
        )
        new_login = APIClient()
        self.assertEqual(
            new_login.post(
                "/api/v1/auth/login/",
                {"email": "ada@example.com", "password": "another-unique-pass-28"},
                format="json",
            ).status_code,
            200,
        )

    def test_a_session_returns_only_that_account(self):
        for username, email in (("ada", "ada@example.com"), ("grace", "grace@example.com")):
            self.client.post(
                "/api/v1/auth/register/",
                {"username": username, "email": email, "password": "a-long-unique-pass-19"},
                format="json",
            )
        ada = APIClient()
        ada.post(
            "/api/v1/auth/login/",
            {"email": "ada@example.com", "password": "a-long-unique-pass-19"},
            format="json",
        )
        self.assertEqual(ada.get("/api/v1/auth/me/").json()["user"]["email"], "ada@example.com")

    def test_session_header_keeps_one_tab_signed_in_after_another_logs_out(self):
        from django.conf import settings

        User.objects.create_user(
            email="ada@example.com",
            username="ada",
            password="a-long-unique-pass-19",
            role=Role.AUTHOR,
        )
        User.objects.create_user(
            email="grace@example.com",
            username="grace",
            password="a-long-unique-pass-19",
            role=Role.AUTHOR,
        )

        tab_a = APIClient()
        login_a = tab_a.post(
            "/api/v1/auth/login/",
            {"email": "ada@example.com", "password": "a-long-unique-pass-19"},
            format="json",
        )
        key_a = login_a.get("X-Session-Key")
        self.assertTrue(key_a)

        tab_b = APIClient()
        login_b = tab_b.post(
            "/api/v1/auth/login/",
            {"email": "grace@example.com", "password": "a-long-unique-pass-19"},
            format="json",
        )
        key_b = login_b.get("X-Session-Key")
        self.assertTrue(key_b)
        self.assertNotEqual(key_a, key_b)

        cookie_is_b = APIClient()
        cookie_is_b.cookies[settings.SESSION_COOKIE_NAME] = tab_b.cookies[settings.SESSION_COOKIE_NAME].value
        still_ada = cookie_is_b.get("/api/v1/auth/me/", HTTP_X_SESSION_KEY=key_a)
        self.assertEqual(still_ada.status_code, 200)
        self.assertEqual(still_ada.json()["user"]["email"], "ada@example.com")

        tab_b.post("/api/v1/auth/logout/", {}, format="json")
        ada_after = APIClient().get("/api/v1/auth/me/", HTTP_X_SESSION_KEY=key_a)
        self.assertEqual(ada_after.status_code, 200)
        self.assertEqual(ada_after.json()["user"]["email"], "ada@example.com")
        self.assertEqual(APIClient().get("/api/v1/auth/me/", HTTP_X_SESSION_KEY=key_b).status_code, 401)
