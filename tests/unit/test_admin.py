import pytest
from django.contrib.admin import AdminSite

from django_otp_webauthn.admin import WebAuthnCredentialAdmin
from django_otp_webauthn.models import WebAuthnCredential
from tests.factories import WebAuthnAttestationFactory


@pytest.mark.django_db
def test_webauthn_credential_admin__hide_sensitive_data(settings, credential):
    """Verify that the admin hides sensitive data when configured to do so."""
    settings.OTP_ADMIN_HIDE_SENSITIVE_DATA = True
    model_admin = WebAuthnCredentialAdmin(WebAuthnCredential, AdminSite())

    form = model_admin.get_form(None, obj=credential)

    assert "user" in form._meta.fields
    assert "name" in form._meta.fields

    assert "public_key_hex" not in form._meta.fields


@pytest.mark.django_db
def test_webauthn_credential_admin__show_sensitive_data(settings, credential):
    """Verify that the admin shows sensitive data when configured to do so."""
    settings.OTP_ADMIN_HIDE_SENSITIVE_DATA = False
    model_admin = WebAuthnCredentialAdmin(WebAuthnCredential, AdminSite())

    form = model_admin.get_form(None, obj=credential)

    assert "user" in form._meta.fields
    assert "name" in form._meta.fields

    assert "public_key_hex" in form._meta.fields


@pytest.mark.django_db
def test_webauthn_credential_admin__public_key_hex(credential):
    model_admin = WebAuthnCredentialAdmin(WebAuthnCredential, AdminSite())

    value = model_admin.public_key_hex(credential)

    assert value == credential.public_key.hex()


def test_webauthn_credential_admin__no_add_permission():
    """Verify that the admin does not allow adding new credentials."""
    model_admin = WebAuthnCredentialAdmin(WebAuthnCredential, AdminSite())

    assert model_admin.has_add_permission(None) is False


@pytest.mark.django_db
def test_webauthn_credential_admin__get_queryset_no_nplusone_queries(
    django_assert_max_num_queries,
):
    """Verify that the admin is fast because it doesn't do N+1 queries."""
    model_admin = WebAuthnCredentialAdmin(WebAuthnCredential, AdminSite())

    WebAuthnAttestationFactory.create_batch(10)

    with django_assert_max_num_queries(1):
        creds = model_admin.get_queryset(None).all()

        # Force evaluation of the queryset, including the related fields
        [str(x) for x in creds]
