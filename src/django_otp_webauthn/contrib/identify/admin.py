from typing import TYPE_CHECKING

from django.contrib import admin
from django.utils.safestring import SafeString
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from django_otp_webauthn.models import AbstractWebAuthnCredential


def _identify():
    from django_otp_webauthn.contrib.identify import identify_passkey

    return identify_passkey


class AuthenticatorThumbnailMixin:
    """
    Mixin for Django admin classes to display a thumbnail of the WebAuthn credential icon.

    Usage:
        class MyAdmin(AuthenticatorThumbnailMixin, admin.ModelAdmin):
            list_display = ['credential_icon_thumbnail', ...]
    """

    @admin.display(description=_("Authenticator Icon"))
    def credential_icon_thumbnail(self, obj) -> SafeString:
        """
        Returns a prefers-color-scheme aware HTML ``<picture>`` tag for the credential icon thumbnail.

        Args:
            obj: The WebAuthn credential object.

        Returns:
            :class:`~django.utils.safestring.SafeString`: An HTML ``<picture>``
            tag with the credential icon thumbnail or a placeholder if not available.
        """

        passkey_descriptor = _identify()(obj.aaguid)
        if not passkey_descriptor:
            return ""

        return passkey_descriptor.picture_html(
            picture_attrs={"class": "credential-icon-thumbnail"}
        )


class AuthenticatorNameMixin:
    """
    Mixin for Django admin classes to display the authenticator name based on the AAGUID.

    Usage:
        class MyAdmin(AuthenticatorNameMixin, admin.ModelAdmin):
            list_display = ['authenticator_name', ...]
    """

    @admin.display(description=_("Authenticator Name (inferred)"))
    def authenticator_name(self, obj: "AbstractWebAuthnCredential") -> str:
        """
        Returns the inferred authenticator name based on the AAGUID.

        Args:
            obj: The WebAuthn credential object.

        Returns:
            str: The inferred authenticator name or a placeholder if not available.
        """
        passkey_descriptor = _identify()(obj.aaguid)
        if not passkey_descriptor:
            return _("Unknown Authenticator")

        return passkey_descriptor.name
