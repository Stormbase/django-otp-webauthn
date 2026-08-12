import pytest
from django.core.management import call_command
from django.core.management.base import SystemCheckError


@pytest.mark.django_db
def test_checks_noop_when_contrib_identify_not_installed(mocker, settings):
    """Verify that the checks no-ops when the contrib.identify module is not installed, even if the check is registered."""
    assert "django_otp_webauthn.contrib.identify" in settings.INSTALLED_APPS
    mocker.patch(
        "django_otp_webauthn.utils.is_contrib_identify_module_enabled",
        return_value=False,
    )

    # Mock not installed, but still the check passes because the identify app is
    # supposedly not installed (but checks are still registered)
    mocker.patch(
        "django_otp_webauthn.contrib.identify.utils.is_identify_passkey_package_installed",
        return_value=False,
    )
    call_command("check")


def test_check_identify_passkey_package_installed(mocker, settings):
    """Verify that a SystemCheckError is raised when the 'identify_passkey' package is not installed."""
    assert "django_otp_webauthn.contrib.identify" in settings.INSTALLED_APPS

    # Mock installed
    mocker.patch(
        "django_otp_webauthn.contrib.identify.utils.is_identify_passkey_package_installed",
        return_value=False,
    )

    with pytest.raises(
        SystemCheckError, match="The 'identify_passkey' package is not installed."
    ):
        call_command("check")

    # Check that no error is raised when the package is installed
    mocker.patch(
        "django_otp_webauthn.contrib.identify.utils.is_identify_passkey_package_installed",
        return_value=True,
    )
    call_command("check")


def test_check_passkey_icon_finder_enabled(settings):
    """Verify that a SystemCheckError is raised when the PasskeyIconsFinder is not enabled."""
    assert "django_otp_webauthn.contrib.identify" in settings.INSTALLED_APPS

    # Remove the PasskeyIconsFinder from STATICFILES_FINDERS
    settings.STATICFILES_FINDERS = tuple(
        finder
        for finder in settings.STATICFILES_FINDERS
        if finder != "django_otp_webauthn.contrib.identify.PasskeyIconsFinder"
    )

    with pytest.raises(
        SystemCheckError,
        match="Static file finder 'django_otp_webauthn.contrib.identify.PasskeyIconsFinder' is not enabled.",
    ):
        call_command("check")

    # Add the PasskeyIconsFinder back to STATICFILES_FINDERS
    settings.STATICFILES_FINDERS += (
        "django_otp_webauthn.contrib.identify.PasskeyIconsFinder",
    )
    call_command("check")

    # Remove the PasskeyIconsFinder and add a subclass of it to STATICFILES_FINDERS
    settings.STATICFILES_FINDERS = tuple(
        finder
        for finder in settings.STATICFILES_FINDERS
        if finder != "django_otp_webauthn.contrib.identify.PasskeyIconsFinder"
    )
    settings.STATICFILES_FINDERS += ("tests.testapp.finders.CustomPasskeyIconsFinder",)
    call_command("check")
