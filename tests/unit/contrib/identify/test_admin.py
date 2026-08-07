import pytest
from bs4 import BeautifulSoup
from django.contrib.admin import AdminSite

from django_otp_webauthn.admin import WebAuthnCredentialAdmin
from django_otp_webauthn.contrib.identify.admin import (
    AuthenticatorNameMixin,
    AuthenticatorThumbnailMixin,
)
from django_otp_webauthn.models import WebAuthnCredential
from tests.factories import APPLE_AAGUID


class AdminWithMixins(
    AuthenticatorNameMixin, AuthenticatorThumbnailMixin, WebAuthnCredentialAdmin
):
    list_display = WebAuthnCredentialAdmin.list_display + [
        "authenticator_name",
        "credential_icon_thumbnail",
    ]


@pytest.mark.django_db
def test_webauthn_credential_modeladmin_mixins__apple(credential):
    """Verify that the admin mixins works correctly for Apple credentials."""

    credential.aaguid = APPLE_AAGUID
    credential.save()
    model_admin = AdminWithMixins(WebAuthnCredential, AdminSite())

    # Test authenticator_name
    name = model_admin.authenticator_name(credential)
    assert name == "Apple Passwords"

    # Test authenticator_thumbnail
    thumbnail_html = model_admin.credential_icon_thumbnail(credential)
    soup = BeautifulSoup(thumbnail_html, "html.parser")
    img_tag = soup.find("img")
    picture_tag = soup.find("picture")
    assert picture_tag is not None
    assert "credential-icon-thumbnail" in picture_tag["class"]

    assert img_tag is not None
    assert img_tag["src"].startswith("/static/django_otp_webauthn/")
    assert img_tag["alt"] == "Apple Passwords"
    assert img_tag["width"] == "32"


@pytest.mark.django_db
def test_webauthn_credential_modeladmin_mixins__unknown(credential):
    """Verify that the admin mixins works correctly for unknown credentials."""
    credential.aaguid = "00000000-0000-0000-0000-000000000000"  # Unknown AAGUID
    credential.save()
    model_admin = AdminWithMixins(WebAuthnCredential, AdminSite())
    thumbnail_html = model_admin.credential_icon_thumbnail(credential)
    assert thumbnail_html == ""  # No icon for unknown AAGUID

    assert model_admin.authenticator_name(credential) == "Unknown Authenticator"
