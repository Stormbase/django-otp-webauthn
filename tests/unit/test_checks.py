import pytest
from django.core.management import call_command
from django.core.management.base import SystemCheckError
from webauthn.helpers.structs import COSEAlgorithmIdentifier


def dummy_callable(*args, **kwargs):
    return "dummy-value"


def test_check_settings_relying_party_id__not_set(settings):
    """Verify that a SystemCheckError is raised when the relying party ID is not set."""
    settings.OTP_WEBAUTHN_RP_ID_CALLABLE = None
    settings.OTP_WEBAUTHN_RP_ID = None

    with pytest.raises(SystemCheckError, match="Relying party ID not configured"):
        call_command("check")


def test_check_settings_relying_party_id__static_value_set(settings):
    """Verify that no SystemCheckError is raised when the relying party ID is set."""
    settings.OTP_WEBAUTHN_RP_ID_CALLABLE = None
    settings.OTP_WEBAUTHN_RP_ID = "example.com"

    call_command("check")


def test_check_settings_relying_party_id__callable_value_set(settings):
    """Verify that no SystemCheckError is raised when the relying party ID is set."""
    settings.OTP_WEBAUTHN_RP_ID_CALLABLE = "tests.unit.test_checks.dummy_callable"
    settings.OTP_WEBAUTHN_RP_ID = None

    call_command("check")


def test_check_settings_relying_party_name__not_set(settings):
    """Verify that a SystemCheckError is raised when the relying party name is not set."""
    settings.OTP_WEBAUTHN_RP_NAME_CALLABLE = None
    settings.OTP_WEBAUTHN_RP_NAME = None

    with pytest.raises(SystemCheckError, match="Relying party name not configured"):
        call_command("check")


def test_check_settings_relying_party_name__static_value_set(settings):
    """Verify that no SystemCheckError is raised when the relying party name is set."""
    settings.OTP_WEBAUTHN_RP_NAME_CALLABLE = None
    settings.OTP_WEBAUTHN_RP_NAME = "example.com"

    call_command("check")


def test_check_settings_relying_party_name__callable_value_set(settings):
    """Verify that no SystemCheckError is raised when the relying party name is set."""
    settings.OTP_WEBAUTHN_RP_NAME_CALLABLE = "tests.unit.test_checks.dummy_callable"
    settings.OTP_WEBAUTHN_RP_NAME = None

    call_command("check")


def test_check_settings_supported_cose_algorithms__none(settings):
    """Verify that no SystemCheckError is raised when OTP_WEBAUTHN_SUPPORTED_COSE_ALGORITHMS=None - defaults will be used."""
    settings.OTP_WEBAUTHN_SUPPORTED_COSE_ALGORITHMS = None

    call_command("check")


def test_check_settings_supported_cose_algorithms__empty_list(settings):
    """Verify that a SystemCheckError is raised when no COSE algorithms are set."""
    settings.OTP_WEBAUTHN_SUPPORTED_COSE_ALGORITHMS = []

    with pytest.raises(SystemCheckError, match="No COSE algorithms configured."):
        call_command("check")


def test_check_settings_supported_cose_algorithms__invalid_algorithm(settings):
    """Verify that a SystemCheckError is raised when an invalid COSE algorithm is set."""
    settings.OTP_WEBAUTHN_SUPPORTED_COSE_ALGORITHMS = [1337]

    with pytest.raises(SystemCheckError, match="Unknown or unsupported COSE algorithm"):
        call_command("check")


def test_check_settings_supported_cose_algorithms__valid_algorithm(settings):
    """Verify that no SystemCheckError is raised when a valid COSE algorithm is set."""
    settings.OTP_WEBAUTHN_SUPPORTED_COSE_ALGORITHMS = [
        COSEAlgorithmIdentifier.ECDSA_SHA_256.value
    ]

    call_command("check")


def test_check_settings_allowed_origins_missing(settings):
    """Verify that a SystemCheckError is raised when no allowed origins are set."""
    settings.OTP_WEBAUTHN_ALLOWED_ORIGINS = []

    with pytest.raises(SystemCheckError, match="No allowed origins configured."):
        call_command("check")


def test_check_settings_allowed_origins_set(settings):
    """Verify that no SystemCheckError is raised when allowed origins are set."""
    settings.OTP_WEBAUTHN_ALLOWED_ORIGINS = ["https://example.com"]

    call_command("check")


def test_check_settings_allowed_origins_misconfigured(settings):
    """Verify that a SystemCheckError is raised when allowed origins are misconfigured."""
    # Not a list
    settings.OTP_WEBAUTHN_ALLOWED_ORIGINS = "example.com"
    with pytest.raises(SystemCheckError, match="Allowed origins must be a list"):
        call_command("check")

    # Missing protocol
    settings.OTP_WEBAUTHN_ALLOWED_ORIGINS = ["example.com"]

    with pytest.raises(
        SystemCheckError, match="Allowed origin 'example.com' is not a secure origin"
    ):
        call_command("check")

    # HTTP is not allowed
    settings.OTP_WEBAUTHN_ALLOWED_ORIGINS = ["http://example.com"]

    with pytest.raises(
        SystemCheckError,
        match="Allowed origin 'http://example.com' is not a secure origin.",
    ):
        call_command("check")

    # Localhost is the only exception to the rule
    settings.OTP_WEBAUTHN_ALLOWED_ORIGINS = ["http://localhost"]
    call_command("check")

    # HTTPS is allowed
    settings.OTP_WEBAUTHN_ALLOWED_ORIGINS = ["https://example.com"]
    call_command("check")


def test_check_settings_dangerous_session_backend_used(settings):
    """Verify that a SystemCheckError is raised when the session backend is dangerous."""

    settings.SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"

    with pytest.raises(
        SystemCheckError, match="You are using the signed cookies session backend"
    ):
        call_command("check")

    settings.SESSION_ENGINE = "django.contrib.sessions.backends.file"
    call_command("check")

    settings.SESSION_ENGINE = "django.contrib.sessions.backends.db"
    call_command("check")
