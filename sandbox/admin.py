from django.conf import settings
from django.contrib.admin import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from django_otp_webauthn.admin import WebAuthnCredentialAdmin
from django_otp_webauthn.contrib.identify.admin import (
    AuthenticatorNameMixin,
    AuthenticatorThumbnailMixin,
)
from django_otp_webauthn.utils import get_attestation_model, get_credential_model

User = get_user_model()
WebAuthnCredential = get_credential_model()
WebAuthnAttestation = get_attestation_model()


class SandboxAdminSite(AdminSite):
    site_header = "Sandbox Administration"
    site_title = "Sandbox Admin"
    index_title = "Sandbox Administration"

    login_template = "django_admin_login.html"


class SandboxCredentialAdmin(
    AuthenticatorThumbnailMixin, AuthenticatorNameMixin, WebAuthnCredentialAdmin
):
    list_display = [
        "user",
        "name",
        "aaguid",
        "authenticator_name",
        "credential_icon_thumbnail",
        "credential_id_sha256",
        "last_used_at",
        "created_at",
    ]


admin_site = SandboxAdminSite(name="sandbox_admin")
admin_site.register(User, UserAdmin)
if settings.USE_CONTRIB_IDENTIFY:
    admin_site.register(WebAuthnCredential, SandboxCredentialAdmin)
else:
    admin_site.register(WebAuthnCredential, WebAuthnCredentialAdmin)
