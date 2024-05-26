from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import APIException


class OTPWebAuthnApiError(APIException):
    pass


class InvalidState(OTPWebAuthnApiError):
    status_code = 400
    default_detail = _("State is missing or invalid. Please begin the operation first before trying to complete it.")
    default_code = "invalid_state"


class UnprocessableEntity(OTPWebAuthnApiError):
    status_code = 422
    default_detail = _("Unprocessable Entity")
    default_code = "unprocessable_request"


class PasswordlessLoginDisabled(OTPWebAuthnApiError):
    status_code = 403
    default_detail = _("Passwordless login is disabled.")
    default_code = "passwordless_login_disabled"


class RegistrationDisabled(OTPWebAuthnApiError):
    status_code = 403
    default_detail = _("Registration is disabled.")
    default_code = "registration_disabled"


class AuthenticationDisabled(OTPWebAuthnApiError):
    status_code = 403
    default_detail = _("Authentication is disabled.")
    default_code = "authentication_disabled"


class LoginRequired(OTPWebAuthnApiError):
    status_code = 403
    default_detail = _("User is not logged in.")
    default_code = "login_required"


class UserDisabled(OTPWebAuthnApiError):
    status_code = 403
    default_detail = _("This user account is marked as disabled.")
    default_code = "user_disabled"


class CredentialDisabled(OTPWebAuthnApiError):
    status_code = 403
    default_detail = _("This Passkey has been marked as disabled.")
    default_code = "credential_disabled"


class CredentialNotFound(OTPWebAuthnApiError):
    status_code = 404
    default_detail = _("The Passkey you tried to use was not found. Perhaps it was removed?")
    default_code = "credential_not_found"
