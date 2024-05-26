from django import template
from django.conf import settings
from django.urls import reverse

from django_otp_webauthn.settings import app_settings
from django_otp_webauthn.utils import get_credential_model

register = template.Library()

WebAuthnCredential = get_credential_model()


def get_configuration(extra_options: dict = {}) -> dict:
    configuration = {
        "autocompleteLoginFieldSelector": None,
        "csrfCookieName": settings.CSRF_COOKIE_NAME,
        "beginAuthenticationUrl": reverse("otp_webauthn:credential-authentication-begin"),
        "completeAuthenticationUrl": reverse("otp_webauthn:credential-authentication-complete"),
        "beginRegistrationUrl": reverse("otp_webauthn:credential-registration-begin"),
        "completeRegistrationUrl": reverse("otp_webauthn:credential-registration-complete"),
    }
    configuration.update(extra_options)

    return configuration


@register.inclusion_tag("django_otp_webauthn/auth_scripts.html", takes_context=True)
def render_otp_webauthn_auth_scripts(context, username_field_selector=None):
    extra_options = {}
    # If passwordless login is allowed, tell the client-side script what the username field selector is
    # so the field can be marked with the autocomplete="webauthn" attribute to indicate passwordless login is available.
    if app_settings.OTP_WEBAUTHN_ALLOW_PASSWORDLESS_LOGIN:
        extra_options["autocompleteLoginFieldSelector"] = username_field_selector
    context["configuration"] = get_configuration(extra_options)

    return context


@register.inclusion_tag("django_otp_webauthn/register_scripts.html", takes_context=True)
def render_otp_webauthn_register_scripts(context):
    context["configuration"] = get_configuration()
    return context
