from django.apps import AppConfig
from django.core.checks import Tags, register
from django.utils.translation import gettext_lazy as _

from django_otp_webauthn import checks


class OtpWebauthnConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_otp_webauthn"
    verbose_name = _("OTP WebAuthn")

    def ready(self):
        register(checks.check_settings_supported_cose_algorithms, Tags.security)
        register(checks.check_settings_dangerous_session_backend_used, Tags.security)
        register(checks.check_settings_allowed_origins_missing, Tags.compatibility)
        register(checks.check_settings_allowed_origins_misconfigured, Tags.compatibility)
        register(checks.check_settings_relying_party, Tags.models)
