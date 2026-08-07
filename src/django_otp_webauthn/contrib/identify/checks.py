from django.conf import settings
from django.core.checks import Error
from django.utils.module_loading import import_string

from django_otp_webauthn.contrib.identify import utils
from django_otp_webauthn.contrib.identify.finders import PasskeyIconsFinder

ERR_IDENTIFY_PASSKEY_PACKAGE_NOT_INSTALLED = "otp_webauthn_identify.E001"


def check_identify_passkey_package_installed(app_configs, **kwargs):
    """Check if the 'identify_passkey' package is installed."""

    errors = []
    if not utils.is_identify_passkey_package_installed():
        errors.append(
            Error(
                "The 'identify_passkey' package is not installed.",
                hint="Did you install django-otp-webauthn with the 'identify' extra? Try: pip install django-otp-webauthn[identify]",
                obj=None,
                id=ERR_IDENTIFY_PASSKEY_PACKAGE_NOT_INSTALLED,
            )
        )
    return errors


def check_passkey_icon_finder_enabled(app_configs, **kwargs):
    """Check if ``django_otp_webauthn.contrib.identify.PasskeyIconsFinder`` (or a subclass) is enabled."""

    errors = []
    # Look for subclasses of PasskeyIconsFinder
    for finder in settings.STATICFILES_FINDERS:
        # No need to handle ModuleNotFoundError, this check won't even run if
        # Django can't lookup the finder class when resolving settings
        finder_class = import_string(finder)
        if issubclass(finder_class, PasskeyIconsFinder):
            break
    else:
        errors.append(
            Error(
                "Static file finder 'django_otp_webauthn.contrib.identify.PasskeyIconsFinder' is not enabled.",
                hint="Add 'django_otp_webauthn.contrib.identify.PasskeyIconsFinder' to your STATICFILES_FINDERS setting.",
                obj=None,
                id="otp_webauthn_identify.E002",
            )
        )
    return errors
