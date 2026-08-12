from django_otp_webauthn.contrib.identify import utils


def test_is_identify_passkey_package_installed__module_not_found(mocker):
    """Verify that is_identify_passkey_package_installed returns False when the identify_passkey package is not installed."""
    mocker.patch("importlib.util.find_spec", side_effect=ModuleNotFoundError)

    assert not utils.is_identify_passkey_package_installed()
