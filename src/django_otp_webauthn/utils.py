from logging import Logger
from typing import TYPE_CHECKING, Optional

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from webauthn.helpers import exceptions as pywebauthn_exceptions

from django_otp_webauthn import exceptions
from django_otp_webauthn.settings import app_settings

if TYPE_CHECKING:
    from .models import AbstractWebAuthnAttestation, AbstractWebAuthnCredential


class rewrite_exceptions:
    """Context manager that swallows py_webauthn exceptions and raises
    appropriate django_otp_webauthn api exceptions that are handled nicely by rest
    framework.

    To aid in debugging, this context manager accepts an optional logger
    argument that will be used to log the py_webauthn exceptions raised.

    """

    def __init__(self, logger: Optional[Logger] = None):
        self.logger = logger

    def log_exception(self, exc: Exception):
        if self.logger:
            self.logger.exception(exc)

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.log_exception(exc_val)
        if exc_type is pywebauthn_exceptions.InvalidCBORData:
            raise exceptions.UnprocessableEntity(code="invalid_cbor", detail="Invalid CBOR data provided.") from exc_val
        elif exc_type is pywebauthn_exceptions.InvalidRegistrationResponse:
            raise exceptions.UnprocessableEntity(
                code="invalid_registration_response",
                detail="Invalid registration response provided.",
            ) from exc_val
        elif exc_type is pywebauthn_exceptions.InvalidAuthenticationResponse:
            raise exceptions.UnprocessableEntity(
                code="invalid_authentication_response",
                detail="Invalid authentication response provided.",
            ) from exc_val
        elif exc_type is pywebauthn_exceptions.InvalidJSONStructure:
            raise exceptions.UnprocessableEntity(
                code="invalid_json_structure",
                detail="There is a problem with the provided JSON data.",
            ) from exc_val
        elif exc_type is pywebauthn_exceptions.UnsupportedAlgorithm:
            raise exceptions.UnprocessableEntity(
                code="unsupported_algorithm",
                detail="The specified COSE algorithm is not supported by this server.",
            ) from exc_val
        elif (
            exc_type is pywebauthn_exceptions.UnsupportedPublicKey
            or exc_type is pywebauthn_exceptions.InvalidPublicKeyStructure
        ):
            raise exceptions.UnprocessableEntity(
                code="unsupported_public_key",
                detail="The public key is malformed or not supported.",
            ) from exc_val
        elif exc_type is pywebauthn_exceptions.InvalidAuthenticatorDataStructure:
            raise exceptions.UnprocessableEntity(
                code="invalid_authenticator_data_structure",
                detail="The provided authenticator data is malformed.",
            ) from exc_val
        elif exc_type is pywebauthn_exceptions.InvalidCertificateChain:
            raise exceptions.UnprocessableEntity(
                code="invalid_certificate_chain",
                detail="The certificate chain in the attestation could not be validated.",
            ) from exc_val
        elif exc_type is pywebauthn_exceptions.UnsupportedEC2Curve:
            raise exceptions.UnprocessableEntity(
                code="unsupported_ec2_curve", detail="The EC2 curve is not supported."
            ) from exc_val
        elif exc_type is pywebauthn_exceptions.InvalidBackupFlags:
            raise exceptions.UnprocessableEntity(
                code="invalid_backup_flags",
                detail="Impossible backup flags combination was provided.",
            ) from exc_val
        return False


def get_exempt_urls() -> list:
    """Returns the list of urls that should be allowed without 2FA verification."""
    return [
        # Registration
        reverse("otp_webauthn:credential-registration-begin"),
        reverse("otp_webauthn:credential-registration-complete"),
        # Login
        reverse("otp_webauthn:credential-authentication-begin"),
        reverse("otp_webauthn:credential-authentication-complete"),
    ]


def get_credential_model() -> "AbstractWebAuthnCredential":
    """Returns the WebAuthnCredential model that is active in this project."""
    # Inspired by Django's django.contrib.auth.get_user_model
    try:
        return apps.get_model(app_settings.OTP_WEBAUTHN_CREDENTIAL_MODEL, require_ready=False)
    except ValueError:
        raise ImproperlyConfigured("OTP_WEBAUTHN_CREDENTIAL_MODEL must be of the form 'app_label.model_name'")
    except LookupError:
        raise ImproperlyConfigured(
            f"OTP_WEBAUTHN_CREDENTIAL_MODEL refers to model '{app_settings.OTP_WEBAUTHN_CREDENTIAL_MODEL}' that has not been installed"
        )


def get_attestation_model() -> "AbstractWebAuthnAttestation":
    """Returns the WebAuthnAttestation model that is active in this project."""

    # Inspired by Django's django.contrib.auth.get_user_model
    try:
        return apps.get_model(app_settings.OTP_WEBAUTHN_ATTESTATION_MODEL, require_ready=False)
    except ValueError:
        raise ImproperlyConfigured("OTP_WEBAUTHN_ATTESTATION_MODEL must be of the form 'app_label.model_name'")
    except LookupError:
        raise ImproperlyConfigured(
            f"OTP_WEBAUTHN_ATTESTATION_MODEL refers to model '{app_settings.OTP_WEBAUTHN_ATTESTATION_MODEL}' that has not been installed"
        )


def get_credential_model_string() -> str:
    """Returns the string representation of the WebAuthnCredential model that is
    active in this project."""
    return app_settings.OTP_WEBAUTHN_CREDENTIAL_MODEL


def get_attestation_model_string() -> str:
    """Returns the string representation of the WebAuthnAttestation model
    that is active in this project."""
    return app_settings.OTP_WEBAUTHN_ATTESTATION_MODEL
