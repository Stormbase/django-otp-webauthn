from django import template
from django.http import HttpRequest
from django.middleware import csrf
from django.urls import reverse
from webauthn.helpers import bytes_to_base64url

from django_otp_webauthn.helpers import WebAuthnHelper
from django_otp_webauthn.settings import app_settings
from django_otp_webauthn.utils import get_credential_model

WebAuthnCredential = get_credential_model()
register = template.Library()


def get_configuration(request: HttpRequest, extra_options: dict = None) -> dict:
    if extra_options is None:
        extra_options = {}
    configuration = {
        "autocompleteLoginFieldSelector": None,
        "nextFieldSelector": "input[name='next']",
        "csrfToken": csrf.get_token(request),
        "removeUnknownCredential": app_settings.OTP_WEBAUTHN_SIGNAL_UNKNOWN_CREDENTIAL,
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


@register.inclusion_tag(
    "django_otp_webauthn/sync_signals_scripts.html", takes_context=True
)
def render_otp_webauthn_sync_signals_scripts(context):
    """Renders a script that calls the
    ``PublicKeyCredential.signalCurrentUserDetails`` and
    ``PublicKeyCredential.signalAllAcceptedCredentials`` browser apis to update user details
    and to hide removed credentials, so they won't be shown in future authentication prompts.

    These scripts are only rendered if the user is authenticated and if a sync is needed.

    A sync can be requested by calling the ``django_otp_webauthn.utils.set_webauthn_sync_signal`` utility function.
    """
    request = context["request"]

    # Bail out if the user is not authenticated
    if not request.user.is_authenticated:
        return {}

    # Bail out if no sync is needed
    if "otp_webauthn_sync_needed" not in request.session:
        return {}

    # Consume the sync needed flag
    request.session.pop("otp_webauthn_sync_needed")

    helper: WebAuthnHelper = WebAuthnCredential.get_webauthn_helper(request)
    user_entity = helper.get_user_entity(request.user)
    rp_id = helper.get_relying_party_domain()

    # Convert all credential ids to base64url-encoded strings, as is needed by
    # the WebAuthn API
    credential_ids = [
        bytes_to_base64url(descriptor.id)
        for descriptor in WebAuthnCredential.get_credential_descriptors_for_user(
            request.user
        )
    ]

    # The data the client-side script uses to signal the browser
    context["configuration"] = {
        "rpId": rp_id,
        "userId": bytes_to_base64url(user_entity.id),
        "name": user_entity.name,
        "displayName": user_entity.display_name,
        "credentialIds": credential_ids,
    }
    return context
