import pytest
from django.apps import apps
from django.core.exceptions import ImproperlyConfigured

from django_otp_webauthn.contrib.identify import PasskeyDescriptor
from django_otp_webauthn.utils import is_contrib_identify_module_enabled
from tests.factories import (
    WebAuthnCredentialFactory,
)


@pytest.mark.django_db
def test_credential_identify():
    """Verify that a WebAuthnCredential can be identified as a PasskeyDescriptor using the identify() method."""
    credential_unknown = WebAuthnCredentialFactory(
        aaguid="00000000-0000-0000-0000-000000000000"
    )
    credential_apple_passwords = WebAuthnCredentialFactory(
        aaguid="fbfc3007-154e-4ecc-8c0b-6e020557d7bd"
    )  # Apple Passwords

    apple_descriptor = credential_apple_passwords.identify()

    assert credential_unknown.identify() is None  # Not able to be identified
    assert apple_descriptor is not None, (
        "This credential should be identified as Apple Passwords, but it was not."
    )
    assert isinstance(apple_descriptor, PasskeyDescriptor)
    assert apple_descriptor.name == "Apple Passwords"
    assert apple_descriptor.aaguid == "fbfc3007-154e-4ecc-8c0b-6e020557d7bd"


@pytest.mark.django_db
def test_credential_inferred_name():
    """Verify that a WebAuthnCredential has a populated inferred_name property when it can be identified."""
    credential_unknown = WebAuthnCredentialFactory(
        aaguid="00000000-0000-0000-0000-000000000000"
    )
    credential_apple_passwords = WebAuthnCredentialFactory(
        aaguid="fbfc3007-154e-4ecc-8c0b-6e020557d7bd"
    )  # Apple Passwords

    assert credential_unknown.inferred_name is None  # Not able to be identified
    assert credential_apple_passwords.inferred_name == "Apple Passwords"


@pytest.mark.django_db
def test_credential_str_representation():
    """Verify that a WebAuthnCredential has a different default __str__ representation when it can be identified."""
    credential_unknown = WebAuthnCredentialFactory(
        name="", aaguid="00000000-0000-0000-0000-000000000000"
    )
    credential_apple_passwords = WebAuthnCredentialFactory(
        name="", aaguid="fbfc3007-154e-4ecc-8c0b-6e020557d7bd"
    )  # Apple Passwords

    assert str(credential_unknown) == f" ({credential_unknown.user})"
    assert (
        str(credential_apple_passwords)
        == f"Apple Passwords ({credential_apple_passwords.user})"
    )

    # But when we set the name explicitly, it should use that instead
    credential_unknown.name = "My Custom Name"
    assert str(credential_unknown) == f"My Custom Name ({credential_unknown.user})"
    credential_apple_passwords.name = "My Custom Name"
    assert (
        str(credential_apple_passwords)
        == f"My Custom Name ({credential_apple_passwords.user})"
    )


@pytest.mark.django_db
def test_credential_identify__identify_app_not_installed(
    settings,
):
    # Remove the identify app from INSTALLED_APPS to simulate it not being installed
    apps.set_installed_apps(
        [
            app
            for app in settings.INSTALLED_APPS
            if app != "django_otp_webauthn.contrib.identify"
        ]
    )
    assert not is_contrib_identify_module_enabled()

    credential = WebAuthnCredentialFactory(
        aaguid="fbfc3007-154e-4ecc-8c0b-6e020557d7bd"
    )  # Apple Passwords
    with pytest.raises(
        ImproperlyConfigured,
        match="django_otp_webauthn.contrib.identify is not installed. Add it to your INSTALLED_APPS to use the identify feature.",
    ):
        credential.identify()

    apps.unset_installed_apps()  # Reset installed apps to original state
