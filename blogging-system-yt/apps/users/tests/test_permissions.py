from django.test import SimpleTestCase
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIRequestFactory

from apps.accounts.models import Role, User
from apps.users.permissions import IsAdmin, IsAuthor, IsOwner


class Owned:
    def __init__(self, author):
        self.author = author


def _user(role):
    user = User(email=f"{role}@example.com", username=role, role=role)
    user.is_active = True
    return user


class RolePermissionTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def _request(self, user):
        request = self.factory.get("/unused/")
        request.user = user
        return request

    def test_author_permission_allows_writers_and_admins(self):
        self.assertTrue(IsAuthor().has_permission(self._request(_user(Role.AUTHOR)), None))
        self.assertTrue(IsAuthor().has_permission(self._request(_user(Role.ADMIN)), None))
        with self.assertRaises(PermissionDenied):
            IsAuthor().has_permission(self._request(_user(Role.READER)), None)

    def test_admin_permission_is_admin_only(self):
        self.assertTrue(IsAdmin().has_permission(self._request(_user(Role.ADMIN)), None))
        with self.assertRaises(PermissionDenied):
            IsAdmin().has_permission(self._request(_user(Role.AUTHOR)), None)

    def test_owner_can_access_only_their_object_and_admin_can_access_any(self):
        author = _user(Role.AUTHOR)
        other = _user(Role.READER)
        admin = _user(Role.ADMIN)
        owned = Owned(author)

        self.assertTrue(IsOwner().has_object_permission(self._request(author), None, owned))
        self.assertFalse(IsOwner().has_object_permission(self._request(other), None, owned))
        self.assertTrue(IsOwner().has_object_permission(self._request(admin), None, owned))
