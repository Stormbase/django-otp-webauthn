from django.conf import settings as django_settings
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from django_otp_webauthn.models import WebAuthnCredential
from django_otp_webauthn.settings import app_settings

credential_model = app_settings.OTP_WEBAUTHN_CREDENTIAL_MODEL


class WebAuthnCredentialAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "name",
        "credential_id_hex_display",
        "aaguid",
        "last_used_at",
        "created_at",
    ]
    list_filter = ["last_used_at", "created_at"]
    raw_id_fields = ["user"]
    readonly_fields = [
        "aaguid",
        "credential_id_hex",
        "public_key_hex",
        "last_used_at",
        "created_at",
        "transports",
        "discoverable",
        "backup_eligible",
        "backup_state",
        "sign_count",
    ]

    # Disable the "Add" button - no use creating credentials manually
    def has_add_permission(self, request, obj=None):
        return False

    def credential_id_hex(self, obj):
        return obj.credential_id.hex()

    def credential_id_hex_display(self, obj):
        """Truncate the credential ID to 64 characters for display in listing."""
        return obj.credential_id.hex()[:64]

    def public_key_hex(self, obj):
        return obj.public_key.hex()

    credential_id_hex_display.admin_order_field = "credential_id"
    credential_id_hex_display.short_description = _("credential ID")
    public_key_hex.short_description = _("COSE public key")

    def get_fieldsets(self, request, obj=None):
        extra_fields = []
        hide_sensitive_data = getattr(django_settings, "OTP_ADMIN_HIDE_SENSITIVE_DATA", False)
        if not hide_sensitive_data and obj:
            extra_fields = ["public_key_hex"]

        configuration_fields = [
            "aaguid",
            "credential_id_hex",
            "transports",
            "discoverable",
            "backup_eligible",
            "backup_state",
            "sign_count",
        ] + extra_fields

        fieldsets = [
            (
                _("Identity"),
                {
                    "fields": ["user", "name", "confirmed"],
                },
            ),
            (
                _("Meta"),
                {
                    "fields": ["last_used_at", "created_at"],
                },
            ),
            (
                _("WebAuthn credential data"),
                {
                    "fields": configuration_fields,
                },
            ),
        ]
        return fieldsets

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related("user")

        return queryset


# Only register our ModelAdmin if the default model is the active WebAuthnCredential model.
# Otherwise, it is up to the developer to register their own ModelAdmin for their custom model.
if credential_model == "django_otp_webauthn.WebAuthnCredential":
    admin.site.register(WebAuthnCredential, WebAuthnCredentialAdmin)
