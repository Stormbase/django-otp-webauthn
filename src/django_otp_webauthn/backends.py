from typing import Any
from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.http import HttpRequest

from django_otp_webauthn.models import AbstractWebAuthnCredential

UserModel = get_user_model()

class WebAuthnBackend:
    """A simple authentication backend used when django_otp_webauthn is used for passwordless authentication"""

    def authenticate(self, request: HttpRequest, web_authn_credential: AbstractWebAuthnCredential | None = None, **kwargs: Any) -> AbstractBaseUser | None:
        if web_authn_credential:
            user = web_authn_credential.user
            return user if self.user_can_authenticate(user) else None
        return None
    
    def get_user(self, user_id) -> AbstractBaseUser | None:
        user = UserModel._default_manager.get(pk=user_id)
        return user if self.user_can_authenticate(user) else None
    
    def user_can_authenticate(self, user: AbstractBaseUser | None) -> bool:
        """
        Reject users with is_active=False. Custom user models that don't have
        that attribute are allowed.
        """
        return bool(user and getattr(user, "is_active", True))
