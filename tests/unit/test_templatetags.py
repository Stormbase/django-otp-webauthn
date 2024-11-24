import json

from bs4 import BeautifulSoup
from django.shortcuts import resolve_url
from django.template import Context, Template
from django.urls import reverse

from django_otp_webauthn.templatetags.otp_webauthn import (
    get_configuration,
)


def test_get_configuration__defaults(rf):
    """Test that the configuration is generated with the default values as expected."""
    request = rf.get("/")
    configuration = get_configuration(request)

    assert configuration["autocompleteLoginFieldSelector"] is None

    assert "csrfToken" in configuration
    # Assert that the URLs are actually resolved
    assert resolve_url(configuration["beginAuthenticationUrl"])
    assert resolve_url(configuration["completeAuthenticationUrl"])
    assert resolve_url(configuration["beginRegistrationUrl"])
    assert resolve_url(configuration["completeRegistrationUrl"])


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
