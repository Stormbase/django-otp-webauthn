from django import template
from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from otp_passkeys.conf import get_setting
from otp_passkeys.utils import get_passkey_model

register = template.Library()

UserPasskeyDevice = get_passkey_model()


def get_messages() -> dict:
    return {
        "registration": {
            "error": {
                "clientSideInvalidDomainError": _(
                    "Error registering Passkey.\n\nThe domain '$domain$' is not allowed to register Passkeys."
                ),
                "clientSideCreationNotAllowedError": _(
                    "Error registering Passkey.\n\nRegistration was cancelled by the user or is not allowed."
                ),
                "clientSideCreationUnknownError": _(
                    "Passkey registration could not be completed.\n\nA unknown client-side error occurred."
                ),
                "clientSideInvalidStateError": _(
                    "Passkey registration could not be completed.\n\nA client-side error occurred. Most likely you already have a passkey registered for this website."
                ),
                "serverError": _(
                    "Passkey registration could not be completed.\n\nThe server returned an error ($status_code$)"
                ),
                "serverUnreachable": _(
                    "Passkey registration could not be completed.\n\nThe server could not be reached."
                ),
            }
        },
        "authentication": {
            "error": {
                "clientSideInvalidDomainError": _(
                    "Error authenticating with Passkey.\n\nThe domain '$domain$' is not allowed to use Passkeys."
                ),
                "clientSideNotAllowedError": _(
                    "Error authenticating with Passkey.\n\nAuthentication was cancelled by the user or is not allowed."
                ),
                "clientSideUnknownError": _(
                    "Passkey authentication could not be completed.\n\nAn unknown client-side error occurred."
                ),
                "serverError": _(
                    "Passkey authentication could not be completed.\n\nThe server returned an error ($status_code$)"
                ),
                "serverUnreachable": _(
                    "Passkey authentication could not be completed.\n\nThe server could not be reached."
                ),
            },
        },
    }


def get_configuration(extra_options: dict = {}) -> dict:
    configuration = {
        "autocompleteLoginFieldSelector": None,
        "csrfCookieName": settings.CSRF_COOKIE_NAME,
        "beginAuthenticationUrl": reverse("otp_passkeys:passkey-authentication-begin"),
        "completeAuthenticationUrl": reverse(
            "otp_passkeys:passkey-authentication-complete"
        ),
        "beginRegistrationUrl": reverse("otp_passkeys:passkey-registration-begin"),
        "completeRegistrationUrl": reverse(
            "otp_passkeys:passkey-registration-complete"
        ),
        "messages": get_messages(),
    }
    configuration.update(extra_options)

    return configuration


@register.inclusion_tag(
    "otp_passkeys/otp_passkeys_auth_scripts.html", takes_context=True
)
def render_otp_passkeys_auth_scripts(context, username_field_selector=None):
    extra_options = {}
    # If passwordless login is allowed, tell the client-side script what the username field selector is
    # so the field can be marked with the autocomplete="webauthn" attribute to indicate passwordless login is available.
    if get_setting("OTP_PASSKEYS_ALLOW_PASSWORDLESS_LOGIN"):
        extra_options["autocompleteLoginFieldSelector"] = username_field_selector
    context["configuration"] = get_configuration(extra_options)

    return context


@register.inclusion_tag(
    "otp_passkeys/otp_passkeys_register_scripts.html", takes_context=True
)
def render_otp_passkeys_register_scripts(context):
    context["configuration"] = get_configuration()

    return context
