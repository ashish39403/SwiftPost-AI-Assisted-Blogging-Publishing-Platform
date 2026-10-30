from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed

from apps.accounts.models import Role, User


def register_account(*, email, username, password, first_name="", last_name=""):
    return User.objects.create_user(
        email=email,
        username=username,
        password=password,
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        role=Role.AUTHOR,
    )


def authenticate_email(request, *, email, password):
    user = authenticate(request, email=email, password=password)
    if user is None or not user.is_active:
        exc = AuthenticationFailed("Invalid email or password.")
        exc.api_code = "AUTHENTICATION_FAILED"
        raise exc
    return user


def change_password(*, user, new_password):
    user.set_password(new_password)
    user.save(update_fields=["password", "updated_at"])
    return user
