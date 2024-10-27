import pytest
from django.core.exceptions import ImproperlyConfigured

from django_otp_webauthn.settings import app_settings

STATIC_VALUE = "foobar"


def test_settings_callable_not_callable(settings):
    """Check that an ImproperlyConfigured exception is raised when a callable setting is not callable."""
    settings.OTP_WEBAUTHN_RP_ID_CALLABLE = "tests.unit.test_settings.STATIC_VALUE"

    with pytest.raises(ImproperlyConfigured):
        app_settings._get_callable_setting("OTP_WEBAUTHN_RP_ID_CALLABLE")
