import pytest


@pytest.fixture(scope="module")
def enable_contrib_identify_app(settings):
    """Enable the 'django_otp_webauthn.contrib.identify' app for testing."""
    settings.INSTALLED_APPS += ("django_otp_webauthn.contrib.identify",)
    settings.STATICFILES_FINDERS += (
        "django_otp_webauthn.contrib.identify.PasskeyIconsFinder",
    )
