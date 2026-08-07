import pytest
from identify_passkey import PASSKEYS

from django_otp_webauthn.contrib.identify import PasskeyIconsFinder


def test_passkeyiconfinder_can_find_static(settings, subtests):
    """Verify that the PasskeyIconsFinder can find static files in the identify_passkey.icons package."""
    assert any(
        finder == "django_otp_webauthn.contrib.identify.PasskeyIconsFinder"
        for finder in settings.STATICFILES_FINDERS
    ), (
        "django_otp_webauthn.contrib.identify.PasskeyIconsFinder is not in STATICFILES_FINDERS"
    )

    finder = PasskeyIconsFinder()

    # Check that any passkey icon in the identify_passkey package can be found by PasskeyIconsFinder
    for _, (name, icon_light, icon_dark) in PASSKEYS.items():
        with subtests.test(msg=f"Icons for {name!r}"):
            for icon in (icon_light, icon_dark):
                if icon is None:
                    pytest.skip(f"No icon for {name!r}")
                icon_path = f"django_otp_webauthn/passkey-icons/{icon}"
                found = finder.find(icon_path)
                assert found, f"Could not find static file for {name} at {icon_path}"


def test_passkeyiconfinder_noops_not_installed(mocker):
    """If `identify_passkey` is not installed, the finder no-ops instead of failing loudly."""
    mocker.patch(
        "django_otp_webauthn.contrib.identify.utils.is_identify_passkey_package_installed",
        return_value=False,
    )
    finder = PasskeyIconsFinder()
    assert (
        finder.find("django_otp_webauthn/passkey-icons/apple-passwords-icon.png") == []
    )
