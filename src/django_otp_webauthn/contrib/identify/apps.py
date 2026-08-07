from django.apps import AppConfig
from django.core.checks import Tags, register
from django.utils.translation import gettext_lazy as _

from django_otp_webauthn.contrib.identify import checks


class OtpWebauthnIdentifyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_otp_webauthn.contrib.identify"
    verbose_name = _("OTP WebAuthn Identify")

    def ready(self):
        # Register system checks
        register(checks.check_identify_passkey_package_installed, Tags.compatibility)
        register(checks.check_passkey_icon_finder_enabled, Tags.compatibility)
