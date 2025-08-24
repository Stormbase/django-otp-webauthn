from django import template
from django.http import HttpRequest
from django.middleware import csrf
from django.urls import reverse

from django_otp_webauthn.settings import app_settings

register = template.Library()


def get_configuration(request: HttpRequest, extra_options: dict = None) -> dict:
    if extra_options is None:
        extra_options = {}
    configuration = {
        "autocompleteLoginFieldSelector": None,
        "nextFieldSelector": "input[name='next']",
        "csrfToken": csrf.get_token(request),
        "beginAuthenticationUrl": reverse(
            "otp_webauthn:credential-authentication-begin"
        ),
        "completeAuthenticationUrl": reverse(
            "otp_webauthn:credential-authentication-complete"
        ),
        "beginRegistrationUrl": reverse("otp_webauthn:credential-registration-begin"),
        "completeRegistrationUrl": reverse(
            "otp_webauthn:credential-registration-complete"
        ),
    }
    configuration.update(extra_options)

    return configuration


@register.inclusion_tag("django_otp_webauthn/auth_scripts.html", takes_context=True)
def render_otp_webauthn_auth_scripts(
    context, username_field_selector=None, next_field_selector=None
):
    request = context["request"]
    extra_options = {}
    # If passwordless login is allowed, tell the client-side script what the username field selector is
    # so the field can be marked with the autocomplete="webauthn" attribute to indicate passwordless login is available.
    if app_settings.OTP_WEBAUTHN_ALLOW_PASSWORDLESS_LOGIN:
        extra_options["autocompleteLoginFieldSelector"] = username_field_selector

    if next_field_selector:
        extra_options["nextFieldSelector"] = next_field_selector

    context["configuration"] = get_configuration(request, extra_options)

    return context


@register.inclusion_tag("django_otp_webauthn/register_scripts.html", takes_context=True)
def render_otp_webauthn_register_scripts(context):
    request = context["request"]
    context["configuration"] = get_configuration(request)
    return context
