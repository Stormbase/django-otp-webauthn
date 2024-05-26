from django.contrib.admin import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from django_otp_webauthn.admin import WebAuthnCredentialAdmin
from django_otp_webauthn.utils import get_credential_model

User = get_user_model()
WebAuthnCredential = get_credential_model()


class SandboxAdminSite(AdminSite):
    site_header = "Sandbox Administration"
    site_title = "Sandbox Admin"
    index_title = "Sandbox Administration"

    login_template = "django_admin_login.html"


admin_site = SandboxAdminSite(name="sandbox_admin")
admin_site.register(User, UserAdmin)
admin_site.register(WebAuthnCredential, WebAuthnCredentialAdmin)
