import hashlib

from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.core import checks
from django.db import models
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.functional import cached_property
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _
from django_otp.models import Device, DeviceManager, TimestampMixin
from webauthn.helpers import parse_attestation_object
from webauthn.helpers.structs import (
    AttestationObject,
    AuthenticatorTransport,
    PublicKeyCredentialDescriptor,
)

from django_otp_webauthn import checks as otp_webauthn_checks
from django_otp_webauthn.settings import app_settings
from django_otp_webauthn.utils import get_credential_model_string

User = get_user_model()


def as_credential_descriptors(queryset: QuerySet["AbstractWebAuthnCredential"]) -> list[PublicKeyCredentialDescriptor]:
    descriptors = []
    for id, raw_transports in queryset:
        transports = []
        for t in raw_transports:
            # Though the spec recommends we SHOULD NOT modify the transports
            # in any way, py_webauthn requires we only pass values from the
            # AuthenticatorTransport enum. We are therefore limited to only
            # returning transports supported by AuthenticatorTransport.

            # Relevant spec link:
            # https://www.w3.org/TR/webauthn-3/#dom-publickeycredentialdescriptor-transports
            # > When registering a new credential, the Relying Party SHOULD
            # > store the value returned from getTransports(). When creating
            # > a PublicKeyCredentialDescriptor for that credential, the
            # > Relying Party SHOULD retrieve that stored value and set it
            # > as the value of the transports member.
            try:
                transports.append(AuthenticatorTransport(t))
            except ValueError:
                pass

        descriptors.append(PublicKeyCredentialDescriptor(id=id, transports=transports))
    return descriptors


class AbstractWebAuthnAttestation(models.Model):
    """Abstract model to store attestation for registered credentials for future reference.

    This model is used to store the attestation object returned by the authenticator during registration.

    See https://www.w3.org/TR/webauthn-3/#sctn-attestation for more information about attestation.
    """

    class Format(models.TextChoices):
        PACKED = "packed", "packed"
        TPM = "tpm", "tpm"
        ANDROID_KEY = "android-key", "android-key"
        ANDROID_SAFETYNET = "android-safetynet", "android-safetynet"
        FIDO_U2F = "fido-u2f", "fido-u2f"
        NONE = "none", "none"

    fmt = models.CharField(max_length=255, verbose_name=_("format"), editable=False, choices=Format.choices)
    """The attestation format used by the authenticator. Extracted from the attestation object for convenience."""

    data = models.BinaryField(verbose_name=_("data"), editable=False)
    """The raw attestation data."""

    client_data_json = models.BinaryField(verbose_name=_("client data JSON"), editable=False)
    """The raw client data JSON, as originally sent by the client.

    This is in binary form to preserve exactly what the client sent. This is
    important because it needs to be byte-for-byte identical in order to verify
    the signature."""

    @classmethod
    def check(cls, **kwargs):
        errors = super().check(**kwargs)

        if not hasattr(cls, 'credential'):
            errors.append(
                checks.Error(
                        "missing 'credential' field",
                        hint=f"Add a field named 'credential' as a OneToOneField relating to {get_credential_model_string()}.",
                        obj=cls,
                        id=otp_webauthn_checks.ERR_ATTESTATION_MISSING_CREDENTIAL_FIELD,
                )
            )
        return errors

    @cached_property
    def attestation_object(self) -> AttestationObject:
        """Return the parsed attestation object."""
        return parse_attestation_object(self.data)

    def __str__(self):
        return f"{self.credential} (fmt={self.fmt})"

    class Meta:
        abstract = True
        verbose_name = _("WebAuthn attestation")
        verbose_name_plural = _("WebAuthn attestations")


class WebAuthnCredentialManager(DeviceManager):
    def as_credential_descriptors(self):
        return as_credential_descriptors(self.values_list("credential_id", "transports"))


class AbstractWebAuthnCredential(TimestampMixin, Device):
    """
    Abstract OTP device that validates against a user's WebAuthn credential.

    See https://www.w3.org/TR/webauthn-3/ for more information about the FIDO 2 Web Authentication standard.
    """

    class Meta:
        abstract = True
        indexes = [
            # Create an index on the credential_id_sha256 field to speed up lookups. Overridable if needed.
            # For example, this index could be replaced by a hash index on databases that support it. Saves index space.
            # Example: django.contrib.postgres.indexes.HashIndex(fields=["credential_id_sha256"], name="%(class)s_sha256_idx"),
            models.Index(fields=["credential_id_sha256"], name="%(class)s_sha256_idx"),
        ]
        verbose_name = _("WebAuthn credential")
        verbose_name_plural = _("WebAuthn credentials")

    def __str__(self):
        if not self.name:
            return f"{self.aaguid} ({self.user})"

        return super().__str__()

    objects = WebAuthnCredentialManager()

    # The following fields are necessary or recommended by the WebAuthn L3 specification.
    # https://www.w3.org/TR/webauthn-3/#credential-record
    class CredentialType(models.TextChoices):
        PUBLIC_KEY = "public-key", _("Public Key")

    # https://www.w3.org/TR/webauthn-3/#abstract-opdef-credential-record-type
    # Always set to "public-key" but here for forward compatibility, as recommended by the spec.
    credential_type = models.CharField(
        _("credential type"),
        max_length=32,
        choices=CredentialType.choices,
        default=CredentialType.PUBLIC_KEY,
        editable=False,
    )

    # https://www.w3.org/TR/webauthn-3/#abstract-opdef-credential-record-id
    credential_id = models.BinaryField(
        max_length=1023,
        # We explicitly DO NOT perform a uniqueness check on this field because checking for uniqueness is
        # often slow (or entirely impossible) for large fields. Instead we rely on the credential_id_sha256 field for enforcing uniqueness.
        unique=False,
        verbose_name=_("credential id data"),
        editable=False,
    )
    """Identifier for the credential, created by the client.

    It is used by the client to discover whether it has a matching credential that can be used to authenticate.

    Some authenticators store a lot of data in this field, which means that the field can be quite large.

    Previous revisions of the WebAuthn spec did not mention a maximum size for this field.
    The L3 revision mentions a maximum size of 1023 bytes.

    See https://github.com/w3c/webauthn/pull/1664 for related discussion.
    """

    # https://www.w3.org/TR/webauthn-3/#abstract-opdef-credential-record-publickey
    public_key = models.BinaryField(max_length=1023, verbose_name=_("COSE public key data"), editable=False)
    """The public key of the credential, encoded in COSE_Key format (binary).

    Specification: https://www.rfc-editor.org/rfc/rfc9052#section-7
    """

    # https://www.w3.org/TR/webauthn-3/#abstract-opdef-credential-record-transports
    transports = models.JSONField(_("transports"), editable=False, default=list)
    """The transports supported by this credential. We keep track of this and
    send it to the client to allow it to make better decisions about which
    credential to use when authenticating. For example, if the client knows that
    the user has a credential that supports USB transport, it can show a message
    like "Please insert your usb key to authenticate".

    Fun fact: Some Yubikeys support NFC and USB transports. A Yubikey registered
    via USB will also be able to authenticate via NFC, and it is nice enough to
    tell us that it supports this!
    """

    # https://www.w3.org/TR/webauthn-3/#abstract-opdef-credential-record-signcount
    # Sign count is used to detect cloning attacks. The sign count is
    # incremented BY THE AUTHENTICATOR every time the credential is used. This has
    # lost most of its meaning because authenticators that back up to the cloud,
    # like Apple's iCloud Keychain, are essentially clones and they do not
    # increment this value. We still keep track of it because it is part of the
    # specification.
    sign_count = models.PositiveIntegerField(
        _("sign count"),
        default=0,
        editable=False,
    )
    """The number of times this credential has been used. This is used to detect cloning attacks.

    Note: in practice, this is zero for most cross-platform authenticators like Apple's iCloud Keychain.
    """

    # The level 3 specification also recommends a backupEligible and backupState fields.
    # https://www.w3.org/TR/webauthn-3/#abstract-opdef-credential-record-backupeligible
    # https://www.w3.org/TR/webauthn-3/#abstract-opdef-credential-record-backupstate
    # The idea the spec proposes is to use the backup fields to determine if a
    # credential is at risk of being lost. If there is no risk of loss, traditional
    # password-based authentication could be disabled.
    #
    # Related discussion: https://github.com/w3c/webauthn/issues/1692
    backup_eligible = models.BooleanField(
        _("backup eligible"),
        default=False,
        editable=False,
    )
    """Whether this credential can be backed up.

    This is a hint from the client that the credential implements some mechanism to prevent loss. For example, a cloud backup.
    """

    backup_state = models.BooleanField(
        _("backup state"),
        default=False,
        editable=False,
    )
    """Whether this credential is currently backed up.

    This is a hint from the client that the credential is currently backed up,
    to a cloud account for example. It differs from `backup_eligible` in that
    it indicates the current state of the backup, not just whether it is
    possible.
    """

    # The spec also recommends a uvInitialized field.
    # https://www.w3.org/TR/webauthn-3/#abstract-opdef-credential-record-uvinitialized
    # The idea behind uvInitialized is to keep track of whether this
    # authenticator supports user verification. Apparently, it is meant to be
    # used to influence policy decisions though it is unclear to me how this
    # would work exactly and what benefit it would bring. Our implementation
    # does not use this field. And because it appears it could be added later
    # without too much difficulty, we do not implement it yet.

    aaguid = models.CharField(
        max_length=36,
        verbose_name=_("AAGUID"),
        editable=False,
    )
    """The AAGUID of the authenticator. It can be used to identify the make and
    model of the authenticator but is often zeroed out to protect user
    privacy.

    You may use this field to identify the authenticator, if you are able to.

    The FIDO Alliance maintains a metadata service that may be of use:
    https://fidoalliance.org/metadata/

    Check out this community-maintained list of known AAGUIDs:
    https://github.com/passkeydeveloper/passkey-authenticator-aaguids
    """

    credential_id_sha256 = models.CharField(
        _("hashed credential id"),
        max_length=64,
        editable=False,
        unique=True,
    )

    """SHA256 hash of the credential ID. It is used to speed up lookups for a
    given credential ID only and has no purpose beyond that."""

    discoverable = models.BooleanField(
        _("discoverable"),
        default=None,
        null=True,
        editable=False,
    )
    """Hint provided by the client upon registration on whether this credential
    can be used without us - the relying party - having to provide the
    credential id back to the authenticator.

    Some authenticators, notably limited memory devices like security keys, will
    encode data in the credential id field and need that data again to be able
    to generate signatures. If this is the case, the authenticator cannot be
    used for passwordless login because we'd need a username to look up the
    associated credential ids. If we respond with credential ids, this leaks
    information about the existence of said user account in our system.

    Non-discoverable authenticators can still be used as a second factor during
    MFA, as the client has already submitted some proof of identity so we can
    reasonably provide credential ids back to the client for the authenticator
    to use.

    - `None` = unknown, the client did not provide the hint.
    - `True` = the client hints that the authenticator is usable without
      providing the credential id. The spec calls this a 'Client-side
      discoverable Credential Source'
    - `False` = the client hints that the authenticator cannot function without
      the credential id. The spec calls this a 'Server-side Public Key
      Credential Source'

    For more information see:
    https://www.w3.org/TR/webauthn-3/#client-side-discoverable-public-key-credential-source
    """

    def save(self, *args, **kwargs):
        if not self.credential_id_sha256:
            self.credential_id_sha256 = self.get_credential_id_sha256(self.credential_id)
        super().save(*args, **kwargs)

    @classmethod
    def get_by_credential_id(cls, credential_id: bytes) -> "WebAuthnCredential":
        """Return a WebAuthnCredential instance by its credential id.

        Will attempt to find a matching device by looking up the hash of the credential id.
        """
        hashed_credential_id = cls.get_credential_id_sha256(credential_id)
        return cls.objects.get(credential_id_sha256=hashed_credential_id)

    @classmethod
    def get_credential_id_sha256(cls, credential_id: bytes) -> str:
        """Return the SHA256 hash of the given credential id."""
        return hashlib.sha256(credential_id).hexdigest()

    @classmethod
    def get_credential_descriptors_for_user(cls, user: AbstractBaseUser) -> list[PublicKeyCredentialDescriptor]:
        """Return a list of PublicKeyCredentialDescriptor objects for the given user.

        Each PublicKeyCredentialDescriptor object represents a credential that the
        user has registered.

        These descriptors are intended to inform the client about credential the
        user has registered with the server.
        """

        queryset = (
            cls.objects.filter(user=user)
            # The ordering caries significance. Clients MAY use the order of the
            # list to determine the order in which to display suggested options
            # to the user. We don't explicitly keep track of preferred devices,
            # but we can make the assumption that the most recently used device
            # is most likely to be a preferred device.
            # Source: https://www.w3.org/TR/webauthn-3/#dom-publickeycredentialrequestoptions-allowcredentials
            # > The list is ordered in descending order of preference: the first
            # > item in the list is the most preferred credential, and the last
            # > is the least preferred.
            .order_by(models.F("last_used_at").desc(nulls_last=True))
            .values_list("credential_id", "transports")
        )

        return as_credential_descriptors(queryset)

    @classmethod
    def get_webauthn_helper(cls, request: HttpRequest):
        """Return the WebAuthnHelper class instance for this device."""

        helper = import_string(app_settings.OTP_WEBAUTHN_HELPER_CLASS)
        return helper(request=request)


class WebAuthnCredential(AbstractWebAuthnCredential):
    """A OTP device that validates against a user's credential.

    See https://www.w3.org/TR/webauthn-3/ for more information about the FIDO 2
    Web Authentication standard.
    """

    pass


class WebAuthnAttestation(AbstractWebAuthnAttestation):
    """Model to store attestation for registered credentials for future reference"""

    credential = models.OneToOneField(
        to="django_otp_webauthn.WebAuthnCredential",
        on_delete=models.CASCADE,
        related_name="attestation",
        verbose_name=_("credential"),
        editable=False,
    )
