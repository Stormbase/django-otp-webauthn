import json

import pytest
from bs4 import BeautifulSoup
from django.shortcuts import resolve_url
from django.template import Context, Template
from django.urls import reverse

from django_otp_webauthn.templatetags.otp_webauthn import (
    get_configuration,
)
from django_otp_webauthn.utils import request_user_details_sync
from tests.factories import WebAuthnCredentialFactory, WebAuthnUserHandleFactory


def test_get_configuration__defaults(rf):
    """Test that the configuration is generated with the default values as expected."""
    request = rf.get("/")
    configuration = get_configuration(request)

    assert configuration["autocompleteLoginFieldSelector"] is None

    assert "csrfToken" in configuration
    assert configuration["nextFieldSelector"] == "input[name='next']"
    assert configuration["removeUnknownCredential"] is True
    # Assert that the URLs are actually resolved
    assert resolve_url(configuration["beginAuthenticationUrl"])
    assert resolve_url(configuration["completeAuthenticationUrl"])
    assert resolve_url(configuration["beginRegistrationUrl"])
    assert resolve_url(configuration["completeRegistrationUrl"])


def test_get_configuration__disable_signal_unknown_credential(rf, settings):
    """Test that the configuration reflects the setting to disable signaling unknown credentials."""
    settings.OTP_WEBAUTHN_SIGNAL_UNKNOWN_CREDENTIAL = False
    request = rf.get("/")
    configuration = get_configuration(request)

    assert configuration["removeUnknownCredential"] is False


def test_get_configuration__extra_options(rf):
    """Test that extra options are added to the configuration."""
    request = rf.get("/")
    configuration = get_configuration(request, {"foo": "bar"})

    assert configuration["foo"] == "bar"


def test_render_otp_webauthn_register_scripts(rf):
    request = rf.get("/")
    context = Context({"request": request})
    template = Template(
        "{% load otp_webauthn %}{% render_otp_webauthn_register_scripts %}"
    )
    rendered = template.render(context)

    soup = BeautifulSoup(rendered, "html.parser")
    config = soup.select_one("script[id=otp_webauthn_config]")
    assert config
    assert json.loads(config.text)

    i18n_url = reverse("otp_webauthn:js-i18n-catalog")

    assert soup.select_one(f'script[src="{i18n_url}"]')
    assert soup.select_one('script[src$="otp_webauthn_register.js"]')


def test_render_otp_webauthn_auth_scripts__custom_next_selector(rf, settings):
    settings.OTP_WEBAUTHN_ALLOW_PASSWORDLESS_LOGIN = True
    request = rf.get("/")
    context = Context({"request": request})
    template = Template(
        "{% load otp_webauthn %}{% render_otp_webauthn_auth_scripts next_field_selector=\"input[name='volgende']\" %}"
    )
    rendered = template.render(context)

    soup = BeautifulSoup(rendered, "html.parser")
    config = soup.select_one("script[id=otp_webauthn_config]")
    config = json.loads(config.text)
    assert config["nextFieldSelector"] == "input[name='volgende']"


def test_render_otp_webauthn_auth_scripts__allow_passwordless(rf, settings):
    settings.OTP_WEBAUTHN_ALLOW_PASSWORDLESS_LOGIN = True
    request = rf.get("/")
    context = Context({"request": request})
    template = Template(
        "{% load otp_webauthn %}{% render_otp_webauthn_auth_scripts username_field_selector=\"input[name='username']\" %}"
    )
    rendered = template.render(context)

    soup = BeautifulSoup(rendered, "html.parser")
    config = soup.select_one("script[id=otp_webauthn_config]")
    config = json.loads(config.text)
    assert config["autocompleteLoginFieldSelector"] == "input[name='username']"

    i18n_url = reverse("otp_webauthn:js-i18n-catalog")

    assert soup.select_one(f'script[src="{i18n_url}"]')
    assert soup.select_one('script[src$="otp_webauthn_auth.js"]')


def test_render_otp_webauthn_auth_scripts__no_passwordless(rf, settings):
    settings.OTP_WEBAUTHN_ALLOW_PASSWORDLESS_LOGIN = False
    request = rf.get("/")
    context = Context({"request": request})
    template = Template(
        "{% load otp_webauthn %}{% render_otp_webauthn_auth_scripts username_field_selector=\"input[name='username']\" %}"
    )
    rendered = template.render(context)

    soup = BeautifulSoup(rendered, "html.parser")
    config = soup.select_one("script[id=otp_webauthn_config]")
    config = json.loads(config.text)
    assert config["autocompleteLoginFieldSelector"] is None

    i18n_url = reverse("otp_webauthn:js-i18n-catalog")

    assert soup.select_one(f'script[src="{i18n_url}"]')
    assert soup.select_one('script[src$="otp_webauthn_auth.js"]')


def test_render_otp_webauthn_sync_signals_scripts__not_authenticated(client):
    """Test that the sync signals scripts render nothing for anonymous users, even
    if the sync needed flag is set."""
    request = client.request().wsgi_request
    # Set the sync needed flag in the session
    request_user_details_sync(request)

    context = Context({"request": request})
    template = Template(
        "{% load otp_webauthn %}{% render_otp_webauthn_sync_signals_scripts %}"
    )
    rendered = template.render(context)
    # User is not authenticated, so we stay silent and render
    # nothing - even though the sync needed flag is set.
    assert rendered == ""


@pytest.mark.django_db
def test_render_otp_webauthn_sync_signals_scripts__authenticated(
    client, user, settings
):
    """Test that the sync signals scripts render correctly for authenticated users
    when the sync needed flag is set."""
    settings.OTP_WEBAUTHN_RP_ID = "testserver"
    user.username = "testuser"
    user.first_name = "Test"
    user.last_name = "User"
    user.save()

    handle = WebAuthnUserHandleFactory(user=user)
    credential1 = WebAuthnCredentialFactory(user=user)
    credential2_unconfirmed = WebAuthnCredentialFactory(user=user, confirmed=False)
    credential3_other_user = WebAuthnCredentialFactory()

    client.force_login(user)
    request = client.request().wsgi_request
    # Set the sync needed flag in the session
    request_user_details_sync(request)

    context = Context({"request": request})
    template = Template(
        "{% load otp_webauthn %}{% render_otp_webauthn_sync_signals_scripts %}"
    )
    rendered = template.render(context)
    soup = BeautifulSoup(rendered, "html.parser")
    config_el = soup.select_one("script[id=otp_webauthn_sync_signals_config]")
    assert config_el
    config = json.loads(config_el.text)
    assert config["rpId"] == "testserver"
    assert config["userId"] == handle.handle_base64url
    assert config["name"] == "testuser"
    assert config["displayName"] == "Test User (testuser)"

    assert len(config["credentialIds"]) == 2

    assert credential1.credential_id_base64url in config["credentialIds"]
    # Even if (temporarily) unconfirmed, the credential should be included.
    # It might become confirmed again later, so don't cause its removal just yet.
    assert credential2_unconfirmed.credential_id_base64url in config["credentialIds"]

    # Definitely do not include credentials of other users
    assert credential3_other_user.credential_id_base64url not in config["credentialIds"]

    # But if we render again, the flag should have been consumed and we stay
    # silent this time
    assert "otp_webauthn_sync_needed" not in request.session

    rendered = template.render(context)
    # We did not set the sync needed flag, so we stay silent and render nothing
    assert rendered == ""
