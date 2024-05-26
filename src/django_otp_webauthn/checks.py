from django.conf import settings
from django.core.checks import Error
from webauthn.helpers.structs import COSEAlgorithmIdentifier

from django_otp_webauthn.settings import app_settings

ERR_NO_RP_ID = "otp_webauthn.E010"
ERR_NO_RP_NAME = "otp_webauthn.E011"
ERR_UNSUPPORTED_COSE_ALGORITHM = "otp_webauthn.E020"
ERR_NO_ALLOWED_ORIGINS = "otp_webauthn.E030"
ERR_ALLOWED_ORIGINS_MALFORMED = "otp_webauthn.E031"
ERR_DANGEROUS_SESSION_BACKEND = "otp_webauthn.E040"


def check_settings_relying_party(app_configs, **kwargs):
    errors = []

    if not app_settings.OTP_WEBAUTHN_RP_ID_CALLABLE and not app_settings.OTP_WEBAUTHN_RP_ID:
        errors.append(
            Error(
                "Relying party ID not configured.",
                hint="Set the OTP_WEBAUTHN_RP_ID setting to the main domain of the web application, e.g. 'example.com'.",
                obj=None,
                id=ERR_NO_RP_ID,
            )
        )

    if not app_settings.OTP_WEBAUTHN_RP_NAME_CALLABLE and not app_settings.OTP_WEBAUTHN_RP_NAME:
        errors.append(
            Error(
                "Relying party name not configured.",
                hint="Set the OTP_WEBAUTHN_RP_NAME setting to a human-readable name for the relying party, e.g. 'Acme Corp.'.",
                obj=None,
                id=ERR_NO_RP_NAME,
            )
        )

    return errors


def check_settings_supported_cose_algorithms(app_configs, **kwargs):
    errors = []
    algorithms = app_settings.OTP_WEBAUTHN_SUPPORTED_COSE_ALGORITHMS

    # No need to check - no explicit algorithms provided
    if algorithms == "all":
        return []

    unsupported_algorithms = []
    for algorithm in algorithms:
        if algorithm not in COSEAlgorithmIdentifier:
            unsupported_algorithms.append(algorithm)

    if unsupported_algorithms:
        errors.append(
            Error(
                f"Unknown or unsupported COSE algorithm(s) detected in settings: {unsupported_algorithms!r}",
                hint="Check that the OTP_WEBAUTHN_SUPPORTED_COSE_ALGORITHMS setting only contains COSE algorithm identifier values that are supported.",
                obj=None,
                id=ERR_UNSUPPORTED_COSE_ALGORITHM,
            )
        )
    return errors


def check_settings_allowed_origins_missing(app_configs, **kwargs):
    errors = []
    allowed_origins = app_settings.OTP_WEBAUTHN_ALLOWED_ORIGINS

    if not allowed_origins:
        errors.append(
            Error(
                "No allowed origins configured.",
                hint="Set the OTP_WEBAUTHN_ALLOWED_ORIGINS setting to a list of allowed origins. Origins should be in the format 'https://example.com'.",
                obj=None,
                id=ERR_NO_ALLOWED_ORIGINS,
            )
        )
    return errors


def check_settings_allowed_origins_misconfigured(app_configs, **kwargs):
    errors = []
    allowed_origins = app_settings.OTP_WEBAUTHN_ALLOWED_ORIGINS

    if not allowed_origins:
        return []

    if not isinstance(allowed_origins, list):
        errors.append(
            Error(
                "Allowed origins are not a list.",
                hint="Allowed origins should be a list of strings. Check the OTP_WEBAUTHN_ALLOWED_ORIGINS setting.",
                obj=None,
                id=ERR_ALLOWED_ORIGINS_MALFORMED,
            )
        )
        return errors

    for origin in allowed_origins:
        if not origin.startswith("https://") and not origin.startswith("http://localhost"):
            errors.append(
                Error(
                    f"Allowed origin {origin!r} is not a secure origin.",
                    hint="Expected origins should start with 'https://'. Check the OTP_WEBAUTHN_ALLOWED_ORIGINS setting.",
                    obj=None,
                    id=ERR_ALLOWED_ORIGINS_MALFORMED,
                )
            )

    return errors


def check_settings_dangerous_session_backend_used(app_configs, **kwargs):
    errors = []
    session_engine = settings.SESSION_ENGINE

    if session_engine == "django.contrib.sessions.backends.signed_cookies":
        errors.append(
            Error(
                "You are using the signed cookies session backend. This is an unsupported configuration because it leaves your application vulnerable to replay attacks.",
                hint="Set SESSION_ENGINE to a more secure backend, such as a database, cache or file-based backend.",
                obj=None,
                id=ERR_DANGEROUS_SESSION_BACKEND,
            )
        )
    return errors
