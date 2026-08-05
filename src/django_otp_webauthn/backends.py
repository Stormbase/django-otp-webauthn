from typing import Any, Optional

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.base_user import AbstractBaseUser
from django.http import HttpRequest

from django_otp_webauthn.models import AbstractWebAuthnCredential
from django_otp_webauthn.utils import get_credential_model

UserModel = get_user_model()


class WebAuthnBackend:
    """A simple authentication backend used when django_otp_webauthn is used for passwordless authentication."""

    def authenticate(
        self,
        request: HttpRequest,
        webauthn_credential: Optional[AbstractWebAuthnCredential] = None,
        **kwargs: Any,
    ) -> Optional[AbstractBaseUser]:
        if webauthn_credential:
            user = webauthn_credential.user
            return user if self.user_can_authenticate(user) else None
        return None

    def get_user(self, user_id) -> Optional[AbstractBaseUser]:
        try:
            user = UserModel._default_manager.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
        return user if self.user_can_authenticate(user) else None

    def user_can_authenticate(self, user: Optional[AbstractBaseUser]) -> bool:
        """
        Reject users with is_active=False. Custom user models that don't have
        that attribute are allowed.
        """
        return bool(user and getattr(user, "is_active", True))


class UnenrolledAuthenticationMixin:
    """Mixin for backend to authenticate users only if they are not enrolled with any
    WebAuthn credentials.
    """

    def authenticate(self, request, **kwargs):
        user = super().authenticate(request, **kwargs)
        if user is not None and _has_confirmed_credential(user):
            return None
        return user


class UnenrolledModelBackend(UnenrolledAuthenticationMixin, ModelBackend):
    """A drop-in replacement for ModelBackend that only authenticates users who are not
    enrolled with any WebAuthn credentials.

    Intended for use with passwordless authentication to prevent password-based attacks
    against users enrolled with WebAuthn credentials.
    """


def _has_confirmed_credential(user):
    """Returns True if the user has a confirmed WebAuthn credential."""
    return get_credential_model().objects.filter(user=user, confirmed=True).exists()
