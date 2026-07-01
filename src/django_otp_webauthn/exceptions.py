from django.utils.translation import gettext_lazy as _


class OTPWebAuthnApiError(Exception):
    status_code = 500
    default_detail = _("Error processing WebAuthn request.")
    default_code = "error"

    def __init__(self, detail=None, code=None):
        self.detail = detail or self.default_detail
        self.code = code or self.default_code

    def __str__(self):
        return str(self.detail)


class MalformedRequest(OTPWebAuthnApiError):
    status_code = 400
    default_detail = _("Malformed request. JSON not parsable.")
    default_code = "malformed_request"


class InvalidState(OTPWebAuthnApiError):
    status_code = 400
    default_detail = _(
        "State is missing or invalid. Please begin the operation first before trying to complete it."
    )
    default_code = "invalid_state"


class UnprocessableEntity(OTPWebAuthnApiError):
    status_code = 422
    default_detail = _("Unprocessable Entity")
    default_code = "unprocessable_request"


class PasswordlessLoginDisabled(OTPWebAuthnApiError):
    status_code = 403
    default_detail = _("Passwordless login is disabled.")
    default_code = "passwordless_login_disabled"


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
    default_detail = _(
        "The Passkey you tried to use was not found. Perhaps it was removed?"
    )
    default_code = "credential_not_found"


class CredentialUserMismatch(OTPWebAuthnApiError):
    status_code = 403
    default_detail = _(
        "The Passkey you tried to use does not belong to the currently logged-in user. Try using a different Passkey or logout first to use this Passkey."
    )
    default_code = "credential_user_mismatch"


class NotAuthenticated(OTPWebAuthnApiError):
    status_code = 403
    default_detail = _("Authentication required.")
    default_code = "not_authenticated"
