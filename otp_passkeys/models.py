import hashlib
from typing import Dict, List, Optional, Tuple

from django.contrib.auth import get_user_model
from django.db import models
from django.http import HttpRequest
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_otp.models import Device
from fido2 import cbor
from fido2.cose import CoseKey
from fido2.webauthn import (
    Aaguid,
    AttestedCredentialData,
    AuthenticatorData,
    PublicKeyCredentialDescriptor,
    PublicKeyCredentialType,
)

from .fido_webauthn.provider import FidoProvider

User = get_user_model()


class UserPasskeyDevice(Device):
    """
    A OTP device that validates against a user's passkey.

    See https://www.w3.org/TR/webauthn-3/ for more information about the FIDO 2 Web Authentication standard.
    """

    class AuthenticatorAttachment(models.TextChoices):
        # See: https://www.w3.org/TR/webauthn-3/#authenticator-attachment-modality
        # Cross-platform authenticators (also known as roaming authenticators) are devices that are removable from the client device and can be used with multiple client devices.
        # For example: USB keys, NFC keys, Bluetooth keys, Smartphones, etc.
        CROSS_PLATFORM = "cross-platform", "cross-platform"

        # Platform authenticators are authenticators that are bound to a single client device and cannot be used with other client devices.
        # For example: A TPM chip, a built-in fingerprint reader, etc.
        PLATFORM = "platform", "platform"

    class Meta:
        swappable = "OTP_PASSKEYS_MODEL"
        verbose_name = _("passkey device")
        verbose_name_plural = _("passkey devices")

    def __str__(self):
        if not self.name:
            return "{} ({})".format(self.get_aaguid(), self.user)

        return super().__str__()

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("created at"))
    """When was this passkey created."""
    last_used_at = models.DateTimeField(null=True, verbose_name=_("last used at"))
    """When was this passkey last used successfully."""

    flags = models.PositiveSmallIntegerField(_("flags"), editable=False)
    """Flags for the passkey.

    The flags are a bit field that contains various metadata about the passkey.
    Like whether it is backed-up or not, whether it supports user verification, etc.

    Some flags have convenience methods to make them easier to read.
    For example: `is_backup_eligible` and `is_capable_of_user_verification`.

    See https://www.w3.org/TR/webauthn-3/#authdata-flags
    """
    aaguid = models.BinaryField(
        max_length=16,
        verbose_name=_("aaguid data"),
        editable=False,
        help_text=_(
            "The AAGUID of the authenticator. It can be used to identify the make and model of the authenticator but is often zeroed out to protect user privacy."
        ),
    )
    """The AAGUID of the authenticator. It can be used to identify the make and model of the authenticator but is often zeroed out to protect user privacy.

    You may use this field to identify the authenticator, if you are able to. The FIDO Alliance maintains a metadata service that may be of use: https://fidoalliance.org/metadata/
    Check out this community-maintained list of known AAGUIDs: https://github.com/passkeydeveloper/passkey-authenticator-aaguids
    """

    credential_id = models.BinaryField(
        max_length=1023,
        # We explicitly DO NOT perform a uniqueness check on this field because checking for uniqueness is
        # often slow (or entirely not possible) for large fields. Instead we rely on the credential_id_md5 field for enforcing uniqueness.
        unique=False,
        verbose_name=_("credential id data"),
        editable=False,
    )
    """Identifier for the passkey, created by the client.

    It is used by the client to discover whether it has a matching passkey that can be used to authenticate.

    Some authenticators store a lot of data in this field, which means that the field can be quite large.

    Previous revisions of the WebAuthn spec did not mention a maximum size for this field. 
    Newer (working draft) revisions of the spec have clarified that the maximum size to expect is 1023 bytes, which seems like a reasonable limit to enforce.

    See https://github.com/w3c/webauthn/pull/1664 for the discussion.
    """

    credential_id_md5 = models.BinaryField(
        _("hashed credential id"),
        max_length=32,
        editable=False,
        unique=True,
        db_index=True,
    )
    """MD5 hash of the credential ID. It is used to speed up lookups for a given credential ID only and has no purpose beyond that."""

    cose_public_key = models.BinaryField(
        max_length=1023, verbose_name=_("COSE public key data"), editable=False
    )
    """The public key of the passkey, encoded in COSE_Key format (binary).

    Specification: https://www.rfc-editor.org/rfc/rfc9052#section-7
    """
    transports = models.JSONField(_("transports"), editable=False, default=list)
    """The transports supported by this passkey. We keep track of this and send it to the client to allow it to make better decisions about which passkey to use when authenticating.
    For example, if the client knows that the user has a passkey that supports USB transport, it can show a message like "Please insert your usb key to authenticate".

    Fun fact: Some Yubikeys support NFC and USB transports. A Yubikey registered via USB will also be able to authenticate via NFC, and it is nice enough to tell us that it supports this!
    """

    authenticator_attachment = models.CharField(
        _("authenticator attachment"),
        max_length=24,
        choices=AuthenticatorAttachment.choices,
        editable=False,
    )

    def save(self, *args, **kwargs):
        if not self.credential_id_md5:
            self.credential_id_md5 = __class__.get_credential_id_md5(self.credential_id)
        super().save(*args, **kwargs)

    def get_aaguid(self) -> Aaguid:
        return Aaguid(self.aaguid)

    def is_backup_eligible(self) -> bool:
        return bool(self.flags & AuthenticatorData.FLAG.BACKUP_ELIGIBILITY)

    def is_capable_of_user_verification(self) -> bool:
        return bool(self.flags & AuthenticatorData.FLAG.USER_VERIFIED)

    # For checkmark display in the admin
    is_backup_eligible.boolean = True
    is_capable_of_user_verification.boolean = True

    def get_cose_key(self) -> CoseKey:
        """Get the COSE public key as a CoseKey object.

        For use with the python-fido2 library.
        """
        key_dict, _ = cbor.decode_from(self.cose_public_key)
        return key_dict

    def as_attested_credential(self) -> AttestedCredentialData:
        """Return this device as an AttestedCredentialData object.

        For use with the python-fido2 library."""
        return AttestedCredentialData.create(
            aaguid=self.aaguid,
            credential_id=self.credential_id,
            public_key=self.get_cose_key(),
        )

    @classmethod
    def get_by_credential_id(cls, credential_id) -> Optional["UserPasskeyDevice"]:
        """Return a UserPasskeyDevice instance by its credential id.

        Will attempt to find a matching device by looking up the hash of the credential id.

        Args:
            credential_id: The credential id to look up.

        Returns:
            A UserPasskeyDevice instance or None if no matching device was found.
        """
        hashed_credential_id = cls.get_credential_id_md5(credential_id)
        return cls.objects.filter(credential_id_md5=hashed_credential_id).first()

    @classmethod
    def get_credential_id_md5(cls, credential_id: bytes) -> bytes:
        """Return the MD5 hash of the given credential id.

        Args:
            credential_id: The credential id to hash.
        Returns:
            The MD5 hash digest (bytes) of the credential id.
        """
        # Not used for secure purposes, so we can use a fast hash function that yields short hashes.
        # We use MD5 because it meets our requirements and the probability of a collision is low enough for our purpose.
        # We set the usedforsecurity parameter to prevent exceptions on FIPS-mode systems that do not allow the use of MD5 for security purposes.
        return hashlib.md5(credential_id, usedforsecurity=False).digest()

    @classmethod
    def get_credential_descriptors_for_user(
        cls, user: User
    ) -> List[PublicKeyCredentialDescriptor]:
        """Return a list of PublicKeyCredentialDescriptor objects for the given user.

        These descriptors are intended be used by the client to present a list of possible options to the user.

        Args:
            user: The user to get the credentials for.

        Returns:
            A list of PublicKeyCredentialDescriptor objects for the given user.
        """

        return [
            PublicKeyCredentialDescriptor(
                type=PublicKeyCredentialType.PUBLIC_KEY, id=id, transports=transports
            )
            for id, transports in cls.objects.filter(user=user, confirmed=True)
            # The ordering caries significance. Clients MAY use the order of the
            # list to determine the order in which to display suggested options to the user.
            # We don't explicitly keep track of preferred devices, but we can make the assumption that
            # the most recently used device is most likely to be a preferred device.
            .order_by(models.F("last_used_at").desc(nulls_last=True)).values_list(
                "credential_id", "transports"
            )
        ]

    @classmethod
    def get_fido_provider(cls) -> FidoProvider:
        return FidoProvider()

    @classmethod
    def get_credential_display_name(self, request: HttpRequest, user: User) -> str:
        """Get the display name for the credential.

        This is used to display a name during registration and authentication.

        The default implementation calls User.get_full_name() and falls back to User.get_username().
        """
        return user.get_full_name() or user.get_username()

    @classmethod
    def authenticate_begin(
        cls, *, request: HttpRequest, user: Optional[User] = None
    ) -> Tuple[Dict, Dict]:
        """Begin the authentication process for a user.

        The options returned by this method should be passed back to the client.
        The state returned by this method should be persisted and passed to `authenticate_complete` later.

        Args:
            request: The request object.
            user: The user that is authenticating with a passkey (optional, defaults to `None`).
        Returns:
            A tuple containing the options and state of the server.
        """
        fido = cls.get_fido_provider()

        kwargs = {}

        # In case the user is not authenticated, we require the client to perform user verification.
        # If the user is already authenticated we explicitly do not require user verification for user convenience.
        # We trust that the user has already verified their identity by logging in, asking them to verify their identity again would be redundant.
        require_user_verification = not user or not user.is_authenticated

        # In case of an authenticated user, we can provide a list of allowed credentials to the client which it can use to determine whether it has a matching passkey.
        # This is useful for example when the user has registered a usb key. The client can then show a message like "Please insert your usb key to authenticate".
        if user and user.is_authenticated:
            kwargs["allowed_credentials"] = cls.get_credential_descriptors_for_user(
                user=user
            )

        options, state = fido.authenticate_begin(
            request=request,
            user=user,
            require_user_verification=require_user_verification,
            **kwargs
        )
        return options, state

    @classmethod
    def authenticate_complete(
        cls,
        *,
        request: HttpRequest,
        state: dict,
        user: Optional[User] = None,
        credential_id: bytes,
        client_data: bytes,
        authenticator_data: bytes,
        signature: bytes
    ) -> "UserPasskeyDevice":
        """Complete the authentication process for a user.

        Expects some data from the client, which is returned by the client as part of the authentication process.

        Args:
            request: The request object.
            state: The state of the server. This is returned by `authenticate_begin`.
            user: The user that is authenticating with a passkey (optional, defaults to `None`).
            credential_id: The credential id specified by the client. Expects bytes.
            client_data: The client data returned by the client. Expects bytes.
            authenticator_data: The authenticator data returned by the client. Expects bytes.
            signature: The signature returned by the client. Expects bytes.
        Returns:
            The UserPasskeyDevice instance that was used to authenticate the user if authentication was successful. Exceptions will be raised otherwise.
        Raises:
            ValueError: If the data is invalid (some examples include: invalid signature, invalid client data, etc.)
            DoesNotExist: If no device was found for the given credential id.
        """

        fido = cls.get_fido_provider()

        # SECURITY NOTE: Credential id is controlled by the client!
        # Even if a credential id given to us by a malicious client were to result in hash collision with the credential
        # of another user (which is unlikely, but possible);
        # No harm would be done because we will verify the signature give to us by the malicious client.
        # If the signature is invalid, we reject the authentication attempt by raising an exception.
        device = cls.get_by_credential_id(credential_id=credential_id)
        if not device:
            raise cls.DoesNotExist("No device found for the given credential id.")
        credential = device.as_attested_credential()

        # All the heavy lifting is done by the python-fido2 library.
        # We call our fido provider wrapper class to prepare the data for use with the library.
        # This may raise ValueError exceptions if the data is invalid, which we propagate to the caller of this method.
        fido.authenticate_complete(
            request=request,
            state=state,
            user=user,
            authenticator_data=authenticator_data,
            signature=signature,
            client_data=client_data,
            credential_id=credential_id,
            credentials=[credential],
        )

        # No exceptions at this point means authentication was successful!
        # Update the last used timestamp
        device.last_used_at = timezone.now()
        device.save(update_fields=["last_used_at"])

        return device

    @classmethod
    def register_begin(cls, *, request: HttpRequest, user: User) -> Tuple[Dict, Dict]:
        fido = cls.get_fido_provider()

        # We don't want to register the same passkey multiple times
        exclude_credentials = cls.get_credential_descriptors_for_user(user=user)

        options, state = fido.register_begin(
            request=request, user=user, credentials=exclude_credentials
        )
        return options, state

    @classmethod
    def register_complete(
        cls,
        *,
        request: HttpRequest,
        state: dict,
        user: User,
        client_data: dict,
        attestation: bytes,
        authenticator_attachment: Optional[AuthenticatorAttachment],
        transports: Optional[List[str]] = None,
        name=""
    ) -> "UserPasskeyDevice":
        """Complete the registration process for a user.

        Args:
            request: The request object.
            state: The state of the server. This is returned by `register_begin`.
            user: The user that is registering a passkey.
            client_data: The client data returned by the client. Expects a dict.
            attestation: The attestation object returned by the client. Expects bytes.
            authenticator_attachment: The authenticator attachment returned by the client. Expects a string.
            transports: The transports this device supports. Expects a list of strings.
            name: A friendly name for the passkey to identify it. Will default to an empty string if not specified.

        Returns:
            A UserPasskeyDevice instance."""

        fido = cls.get_fido_provider()

        auth_data = fido.register_complete(
            request=request,
            state=state,
            client_data=client_data,
            attestation=attestation,
        )

        # Ensure that the authenticator attachment is a valid value.
        authenticator_attachment = cls.AuthenticatorAttachment(authenticator_attachment)

        device = cls(
            confirmed=True,
            name=name,
            user=user,
            authenticator_attachment=authenticator_attachment,
            flags=auth_data.get("flags"),
            # We do not validate the transports because we need to be forward-compatible
            # with future transport types.
            transports=transports,
            credential_id=auth_data.get("credential_id"),
            aaguid=auth_data.get("aaguid"),
            cose_public_key=auth_data.get("cose_public_key"),
        )
        device.save()

        return device
