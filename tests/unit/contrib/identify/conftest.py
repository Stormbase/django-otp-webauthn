import django.template
import pytest
from django.apps import apps
from django.template.utils import EngineHandler


@pytest.fixture(autouse=True)
def enable_contrib_identify_app(settings):
    """Enable the 'django_otp_webauthn.contrib.identify' app for testing."""
    if "django_otp_webauthn.contrib.identify" not in settings.INSTALLED_APPS:
        settings.INSTALLED_APPS += ("django_otp_webauthn.contrib.identify",)
    if (
        "django_otp_webauthn.contrib.identify.PasskeyIconsFinder"
        not in settings.STATICFILES_FINDERS
    ):
        settings.STATICFILES_FINDERS += (
            "django_otp_webauthn.contrib.identify.PasskeyIconsFinder",
        )
    apps.set_installed_apps(settings.INSTALLED_APPS)
    django.template.engines = EngineHandler()
    yield
    apps.unset_installed_apps()
    django.template.engines = EngineHandler()
