from typing import TYPE_CHECKING

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse

from .conf import get_setting

if TYPE_CHECKING:
    from .models import UserPasskeyDevice


def get_exempt_urls() -> list:
    """Returns the list of urls that should be allowed without 2FA verification."""
    return [
        # Registration
        reverse("otp_passkeys:passkey-registration-begin"),
        reverse("otp_passkeys:passkey-registration-complete"),
        # Login
        reverse("otp_passkeys:passkey-authentication-begin"),
        reverse("otp_passkeys:passkey-authentication-complete"),
    ]


def get_passkey_model() -> "UserPasskeyDevice":
    """Returns the UserPasskeyDevice model that is active in this project.

    Inspired by django.contrib.auth.get_user_model"""
    try:
        return apps.get_model(get_setting("OTP_PASSKEYS_MODEL"), require_ready=False)
    except ValueError:
        raise ImproperlyConfigured(
            "OTP_PASSKEYS_MODEL must be of the form 'app_label.model_name'"
        )
    except LookupError:
        raise ImproperlyConfigured(
            "OTP_PASSKEYS_MODEL refers to model '%s' that has not been installed"
            % settings.OTP_PASSKEYS_MODEL
        )
