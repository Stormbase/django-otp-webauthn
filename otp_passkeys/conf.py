from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

DEFAULT_SETTINGS = {
    "OTP_PASSKEYS_MODEL": "otp_passkeys.UserPasskeyDevice",
    # Users may authenticate with just a passkey, no username or password required.
    "OTP_PASSKEYS_ALLOW_PASSWORDLESS_LOGIN": True,
}


def get_setting(key, raise_exception=False, callable_args={}):
    """Get a setting from the settings module or fall back to a default.

    If the setting is a callable, it will be called with the keyword arguments in callable_args.
    If raise_exception is True, an ImproperlyConfigured exception will be raised if the setting is not found and no default exists.
    """
    if not hasattr(settings, key):
        # Check for default settings
        if key in DEFAULT_SETTINGS:
            return DEFAULT_SETTINGS.get(key)
        if raise_exception:
            raise ImproperlyConfigured("You must set {} in your settings".format(key))

    value = getattr(settings, key, None)

    if callable(value):
        value = value(**callable_args)
    return value
