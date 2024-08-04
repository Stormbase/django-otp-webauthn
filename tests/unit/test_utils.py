import pytest
from django.core.exceptions import ImproperlyConfigured
from django.urls import resolve
from webauthn.helpers import exceptions as pywebauthn_exceptions

from django_otp_webauthn import exceptions
from django_otp_webauthn.utils import (
    get_attestation_model,
    get_attestation_model_string,
    get_credential_model,
    get_credential_model_string,
    rewrite_exceptions,
)


def test_get_exempt_urls():
    """Test that the get_exempt_urls method works."""
    from django_otp_webauthn.utils import get_exempt_urls

    urls = get_exempt_urls()
    assert isinstance(urls, list)

    # Check that all urls are resolvable
    for url in urls:
        assert resolve(url)


def test_get_credential_model():
    """Test that the get_credential_model method returns the correct model by default."""
    from django_otp_webauthn.models import WebAuthnCredential

    assert get_credential_model() == WebAuthnCredential


def test_get_credential_model_not_installed(settings):
    """Test that the get_credential_model method raises an error when the setting references a model that is not installed."""
    settings.OTP_WEBAUTHN_CREDENTIAL_MODEL = "invalid.model"

    with pytest.raises(ImproperlyConfigured):
        get_credential_model()


def test_get_credential_model_invalid_format(settings):
    """Test that the get_credential_model method raises an error when the setting value is malformed."""
    settings.OTP_WEBAUTHN_CREDENTIAL_MODEL = "invalid"

    with pytest.raises(ImproperlyConfigured):
        get_credential_model()


def test_get_credential_model_custom(settings):
    """Test that the get_credential_model method returns the correct model when customized."""
    settings.INSTALLED_APPS = ["tests.testapp"]
    settings.OTP_WEBAUTHN_CREDENTIAL_MODEL = "testapp.CustomCredential"
    from tests.testapp.models import CustomCredential

    assert get_credential_model() == CustomCredential


def test_get_credential_model_string(settings):
    """Test that the get_credential_model method returns the correct model."""
    settings.INSTALLED_APPS = ["tests.testapp"]
    settings.OTP_WEBAUTHN_CREDENTIAL_MODEL = "testapp.CustomCredential"
    assert get_credential_model_string() == "testapp.CustomCredential"


def test_get_attestation_model():
    """Test that the get_attestation_model method returns the correct model by default."""
    from django_otp_webauthn.models import WebAuthnAttestation

    assert get_attestation_model() == WebAuthnAttestation


def test_get_attestation_model_not_installed(settings):
    """Test that the get_attestation_model method raises an error when the setting references a model that is not installed."""
    settings.OTP_WEBAUTHN_ATTESTATION_MODEL = "invalid.model"

    with pytest.raises(ImproperlyConfigured):
        get_attestation_model()


def test_get_attestation_model_invalid_format(settings):
    """Test that the get_attestation_model method raises an error when the setting value is malformed."""
    settings.OTP_WEBAUTHN_ATTESTATION_MODEL = "invalid"

    with pytest.raises(ImproperlyConfigured):
        get_attestation_model()


def test_get_attestation_model_custom(settings):
    """Test that the get_attestation_model method returns the correct model when customized."""
    settings.INSTALLED_APPS = ["tests.testapp"]
    settings.OTP_WEBAUTHN_ATTESTATION_MODEL = "testapp.CustomAttestation"
    from tests.testapp.models import CustomAttestation

    assert get_attestation_model() == CustomAttestation


def test_get_attestation_model_string(settings):
    """Test that the get_attestation_model method returns the correct model."""
    settings.INSTALLED_APPS = ["tests.testapp"]
    settings.OTP_WEBAUTHN_ATTESTATION_MODEL = "testapp.CustomAttestation"
    assert get_attestation_model_string() == "testapp.CustomAttestation"


def test_rewrite_exceptions_context_manager_nothing_raised():
    with rewrite_exceptions():
        pass


@pytest.mark.parametrize(
    "exception, expected_code",
    [
        (pywebauthn_exceptions.InvalidCBORData, "invalid_cbor"),
        (
            pywebauthn_exceptions.InvalidRegistrationResponse,
            "invalid_registration_response",
        ),
        (
            pywebauthn_exceptions.InvalidAuthenticationResponse,
            "invalid_authentication_response",
        ),
        (pywebauthn_exceptions.InvalidJSONStructure, "invalid_json_structure"),
        (pywebauthn_exceptions.UnsupportedAlgorithm, "unsupported_algorithm"),
        (pywebauthn_exceptions.UnsupportedPublicKey, "unsupported_public_key"),
        (pywebauthn_exceptions.InvalidPublicKeyStructure, "unsupported_public_key"),
        (
            pywebauthn_exceptions.InvalidAuthenticatorDataStructure,
            "invalid_authenticator_data_structure",
        ),
        (pywebauthn_exceptions.InvalidCertificateChain, "invalid_certificate_chain"),
        (pywebauthn_exceptions.UnsupportedEC2Curve, "unsupported_ec2_curve"),
        (pywebauthn_exceptions.InvalidBackupFlags, "invalid_backup_flags"),
    ],
)
def test_rewrite_exceptions_context_manager(exception, expected_code):
    """Test that the rewrite_exceptions context manager rewrites exceptions correctly."""
    with pytest.raises(exceptions.UnprocessableEntity) as exc_info:
        with rewrite_exceptions():
            raise exception()

    assert exc_info.value.detail.code == expected_code


@pytest.mark.parametrize(
    "exception, expected_code",
    [
        (pywebauthn_exceptions.InvalidCBORData, "invalid_cbor"),
    ],
)
def test_rewrite_exceptions_context_manager_with_logger(
    mocker, exception, expected_code
):
    """Test that the rewrite_exceptions context manager rewrites exceptions correctly and logs them."""
    mock_logger = mocker.Mock()

    with pytest.raises(exceptions.UnprocessableEntity) as exc_info:
        with rewrite_exceptions(logger=mock_logger):
            raise exception()

    assert exc_info.value.detail.code == expected_code
    mock_logger.exception.assert_called_once()
