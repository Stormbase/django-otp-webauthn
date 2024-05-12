# Settings pattern adapted from
# https://overtag.dk/v2/blog/a-settings-pattern-for-reusable-django-apps/
from dataclasses import dataclass
from typing import Callable, Union

from django.conf import settings as django_settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest
from django.utils.module_loading import import_string

settings_prefix = "OTP_WEBAUTHN"


@dataclass(frozen=True)
class AppSettings:
    """Access this instance as ``django_otp_webauthn.settings.app_settings``."""

    OTP_WEBAUTHN_EXCEPTION_LOGGER_NAME = "django_otp_webauthn"
    """The logger name to use for exceptions. Leave blank to disable logging."""

    OTP_WEBAUTHN_CREDENTIAL_MODEL = "django_otp_webauthn.WebAuthnCredential"
    """Format: 'app_label.model_name'. The model to use for webauthn
    credential."""

    OTP_WEBAUTHN_ATTESTATION_MODEL = "django_otp_webauthn.WebAuthnAttestation"
    """Format: 'app_label.model_name'. The model to use for webauthn
    attestation."""

    OTP_WEBAUTHN_ALLOW_PASSWORDLESS_LOGIN = True
    """If true, the default views will allow users to login with just a webauthn
    credential. No username or password required. The user will be marked as
    having passed MFA authentication."""

    OTP_WEBAUTHN_RP_ID: str = ""
    """The relying party ID for webauthn ceremonies. This should be the main
    domain of the web application, e.g. 'example.com'.

    **Important:** registered WebAuthn credentials will be scoped to this
    domain and its subdomains. Changing it will require users to re-register
    their credentials. Migration is NOT possible.
    """

    OTP_WEBAUTHN_RP_ID_CALLABLE: Callable[[HttpRequest], str] = ""
    """Advanced usage. Import path to a callable that returns the relying party ID for webauthn
    ceremonies. The callable should accept a single ``HttpRequest`` argument

    For example: 'my_project.utils.get_rp_id'

    This takes precedence over the ``OTP_WEBAUTHN_RP_ID`` setting.
    """

    OTP_WEBAUTHN_RP_NAME: str = ""
    """The relying party name for webauthn ceremonies. Some clients display this
    value to users. It should be a human-readable name for the relying party.
    For example, 'Acme Corp.'.
    """

    OTP_WEBAUTHN_RP_NAME_CALLABLE: Callable[[HttpRequest], str] = ""
    """Advanced usage. Import path to a callable that returns the relying party
    name for webauthn ceremonies. The callable should accept a single
    ``HttpRequest`` argument.

    For example: 'my_project.utils.get_rp_name'

    This takes precedence over the ``OTP_WEBAUTHN_RP_NAME`` setting.
    """

    OTP_WEBAUTHN_ALLOWED_ORIGINS = ["http://localhost:8000"]
    """A list of allowed origins for webauthn authentication. An origin should be
    in the format 'https://example.com'.

    - Origins must be the same as the relying party ID domain, or a subdomain of the relying party ID.
    - Origins must be secure (https://).
    """

    OTP_WEBAUTHN_SUPPORTED_COSE_ALGORITHMS = "all"
    """A list of COSE algorithms supported by the server. Must be an integer
    value from https://www.iana.org/assignments/cose/cose.xhtml#algorithms. If
    set to the string 'all', the default algorithms from py_webauthn will be
    used."""

    OTP_WEBAUTHN_TIMEOUT_SECONDS = 60 * 5  # 5 minutes
    """The timeout in seconds to request for client-side browser webauthn operations. Default is 5 minutes to
    balance security and usability needs.

    Take care to keep this value reasonable. You ought to follow WCAG 2.2
    accessibility guidelines regarding timeouts. See https://www.w3.org/TR/WCAG22/#enough-time.
    """

    def __getattribute__(self, __name: str):
        # Check if a Django project settings should override the app default.
        # In order to avoid returning any random properties of the django settings, we inspect the prefix firstly.
        if __name.startswith(settings_prefix) and hasattr(django_settings, __name):
            return getattr(django_settings, __name)

        return super().__getattribute__(__name)

    def _get_callable_setting(self, key: str) -> Union[Callable, None]:
        """Imports and returns a callable setting."""

        value = self.__getattribute__(key)

        func = import_string(value)
        if not callable(func):
            raise ImproperlyConfigured(f"{key} must be a callable. Got {repr(func)}.")

        return func


app_settings = AppSettings()
