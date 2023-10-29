from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered
from django.utils.translation import gettext_lazy as _
from django_otp.conf import settings

from .models import UserPasskeyDevice


class UserPasskeyDeviceAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "name",
        "credential_id_hex_display",
        "aaguid_display",
        "last_used_at",
        "created_at",
    ]
    list_filter = ["last_used_at", "created_at"]
    raw_id_fields = ["user"]
    readonly_fields = [
        "aaguid_display",
        "credential_id_hex",
        "cose_public_key_hex",
        "last_used_at",
        "created_at",
        "transports",
        "flags",
        "authenticator_attachment",
        "is_capable_of_user_verification",
        "is_backup_eligible",
    ]

    def aaguid_display(self, obj):
        return str(obj.get_aaguid())

    aaguid_display.admin_order_field = "aaguid"
    aaguid_display.short_description = _("AAGUID")

    def credential_id_hex(self, obj):
        return obj.credential_id.hex()

    def credential_id_hex_display(self, obj):
        """Truncate the credential ID to 64 characters for display in listing."""
        return obj.credential_id.hex()[:64]

    credential_id_hex_display.admin_order_field = "credential_id"
    credential_id_hex_display.short_description = _("credential ID")

    def cose_public_key_hex(self, obj):
        return obj.cose_public_key.hex()

    cose_public_key_hex.description = "ABC"

    def get_fieldsets(self, request, obj=None):
        extra_fields = []
        if not settings.OTP_ADMIN_HIDE_SENSITIVE_DATA and obj:
            extra_fields = ["cose_public_key_hex"]

        configuration_fields = [
            "aaguid_display",
            "credential_id_hex",
            "transports",
            "flags",
            "is_backup_eligible",
            "is_capable_of_user_verification",
            "authenticator_attachment",
        ] + extra_fields

        fieldsets = [
            (
                "Identity",
                {
                    "fields": ["user", "name", "confirmed"],
                },
            ),
            (
                "Meta",
                {
                    "fields": ["last_used_at", "created_at"],
                },
            ),
            (
                "Passkey data",
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


try:
    admin.site.register(UserPasskeyDevice, UserPasskeyDeviceAdmin)
except AlreadyRegistered:
    # A useless exception from a double import
    pass
