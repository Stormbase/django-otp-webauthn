from typing import TYPE_CHECKING

from django_otp_webauthn.contrib.identify.finders import PasskeyIconsFinder
from django_otp_webauthn.contrib.identify.types import PasskeyDescriptor, PasskeyIcon

if TYPE_CHECKING:
    from identify_passkey import PasskeyDescriptor as _InternalPasskeyDescriptor

__all__ = [
    "identify_passkey",
    "PasskeyIconsFinder",
    "PasskeyDescriptor",
    "PasskeyIcon",
]


def _identify_passkey() -> "_InternalPasskeyDescriptor | None":
    from identify_passkey import identify_passkey as _id_passkey

    return _id_passkey


def identify_passkey(aaguid: str) -> PasskeyDescriptor | None:
    """
    Identify the passkey type based on the credential's AAGUID.

    Args:
        aaguid (str): The AAGUID of the WebAuthn credential.

    Returns:
        :class:`PasskeyDescriptor` | None: The identified passkey descriptor or None if not found.
    """
    passkey_descriptor = _identify_passkey()(aaguid)
    if not passkey_descriptor:
        return None

    return PasskeyDescriptor(
        aaguid=passkey_descriptor.aaguid,
        name=passkey_descriptor.name,
        icon_light=PasskeyIcon(ref=passkey_descriptor.icon_light)
        if passkey_descriptor.icon_light
        else None,
        icon_dark=PasskeyIcon(ref=passkey_descriptor.icon_dark)
        if passkey_descriptor.icon_dark
        else None,
    )
