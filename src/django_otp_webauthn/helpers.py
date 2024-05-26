import hashlib
import json
from typing import Optional

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.http import HttpRequest
from webauthn import (
    base64url_to_bytes,
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import (
    generate_challenge,
    parse_attestation_object,
    parse_authentication_credential_json,
    parse_registration_credential_json,
)
from webauthn.helpers.structs import (
    AttestationConveyancePreference,
    AuthenticatorAttachment,
    AuthenticatorSelectionCriteria,
    COSEAlgorithmIdentifier,
    CredentialDeviceType,
    PublicKeyCredentialRpEntity,
    PublicKeyCredentialUserEntity,
    RegistrationCredential,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)
from webauthn.registration.verify_registration_response import VerifiedRegistration

from django_otp_webauthn import exceptions
from django_otp_webauthn.models import (
    AbstractWebAuthnAttestation,
    AbstractWebAuthnCredential,
)
from django_otp_webauthn.settings import app_settings
from django_otp_webauthn.utils import get_attestation_model, get_credential_model

User = get_user_model()
WebAuthnCredential = get_credential_model()
WebAuthnAttestation = get_attestation_model()


class PyWebAuthnProvider:
    """A wrapper class around the PyWebAuthn library."""

    def __init__(self, request: HttpRequest):
        self.request = request

    def generate_challenge(self) -> bytes:
        """Generate a challenge for the client to sign."""
        return generate_challenge()

    def get_relying_party_domain(self) -> str:
        """Get the domain of the relying party.

        This is the domain of your website or company. Like "acme.com".

        The default implementation reads the setting `OTP_WEBAUTHN_RP_ID`.

        See also: https://www.w3.org/TR/webauthn-3/#rp-id
        """
        # The domain for the relying party. The WebAuthn spec calls this the RP
        # ID.
        if app_settings.OTP_WEBAUTHN_RP_ID_CALLABLE:
            func = app_settings._get_callable_setting("OTP_WEBAUTHN_RP_ID_CALLABLE")
            return func(request=self.request)
        return app_settings.OTP_WEBAUTHN_RP_ID

    def get_relying_party_name(self) -> str:
        """Get the name of the relying party. This is the name of your website
        or company. Like "Acme Corporation".

        This is sometimes displayed to the user during credential registration.
        ('do you want to register a credential with Acme Corporation?')

        The default implementation reads the setting `OTP_WEBAUTHN_RP_NAME`.

        See also: https://www.w3.org/TR/webauthn-3/#rp-name
        """
        if app_settings.OTP_WEBAUTHN_RP_NAME_CALLABLE:
            func = app_settings._get_callable_setting("OTP_WEBAUTHN_RP_NAME_CALLABLE")
            return func(request=self.request)
        return app_settings.OTP_WEBAUTHN_RP_NAME

    def get_relying_party(self) -> PublicKeyCredentialRpEntity:
        """Get the relying party entity."""
        return PublicKeyCredentialRpEntity(
            name=self.get_relying_party_name(),
            id=self.get_relying_party_domain(),
        )

    def get_discoverable_credentials_preference(self) -> ResidentKeyRequirement:
        """Determines if we'd like the authenticator to store the credential in
        authenticator memory instead of encrypting and storing it on the the
        server. When stored on the server, the private key is encrypted and
        encoded in the credential ID in an opaque format. In such a case, the
        server must provide the credential ID back to the client before the
        client can authenticate using the credential.

        Storing the credential in the authenticator makes it possible to do full
        passwordless authentication, without the relying party having to provide
        all credential IDs for a given user. Providing credentials to
        unauthenticated users leaks information about the existence of the user
        and their registered credential.

        By default, this is set to 'preferred', which means we'd like the
        authenticator to store the private key + metadata in persistent
        authenticator memory if possible, but it's not required.

        Some devices - like security keys - have limited memory and can't store
        the private key and associated metadata for more than a couple
        credentials. This is why we don't set this to 'required' by default.

        Noteworthy is that some authenticators (like Apple iCloud and Android)
        will always create discoverable credentials. Even if you set this to
        'discouraged'.

        **Note**: historically, this was referred to as "resident keys".
        Resident keys mean the same thing as "discoverable credentials".
        Resident key is now an outdated term used in older versions of the
        WebAuthn spec but it still lives on in some places. This library
        attempts to apply the term "discoverable credentials" consistently.

        For more information about discoverable credentials / resident keys see:
         - https://www.w3.org/TR/webauthn-2/#client-side-discoverable-public-key-credential-source
         - https://developers.yubico.com/WebAuthn/WebAuthn_Developer_Guide/Resident_Keys.html
        """
        return ResidentKeyRequirement.PREFERRED

    def get_attestation_conveyance_preference(self) -> AttestationConveyancePreference:
        """Determines if we'd like the authenticator to send an attestation statement.

        By default this is set to "none", which means we don't want the
        authenticator to send an attestation statement.

        The attestation statement is a signed statement from the authenticator
        that can be used to verify the authenticity of the authenticator. It can
        help answer the following question: "is this authenticator really from
        the manufacturer it claims to be from?".

        An example use case of this could be to ensure only authenticators from
        a certain manufacturer are allowed to register - if that were a
        requirement for your application.

        This package uses py_webauthn which supports verifying attestation
        statements. If you want to use this feature, you can set this to
        "indirect" or "direct".

        For more information about attestation, see: -
        https://www.w3.org/TR/webauthn-2/#attestation-conveyance -
        https://www.w3.org/TR/webauthn-2/#sctn-attestation -
        https://developers.yubico.com/WebAuthn/WebAuthn_Developer_Guide/Attestation.html
        """
        return AttestationConveyancePreference.NONE

    def get_authenticator_attachment_preference(
        self,
    ) -> Optional[AuthenticatorAttachment]:
        """Get the authenticator attachment preference.

        By default, this is set to None, which means we don't have a preference.

        For more information about authenticator attachment, see:
        - https://www.w3.org/TR/webauthn-2/#enumdef-authenticatorattachment
        """
        return None

    def get_credential_display_name(self, user: AbstractUser) -> str:
        """Get the display name for the credential.

        This is used to display a name during registration and authentication.

        The default implementation calls User.get_full_name() and falls back to
        User.get_username().
        """
        return user.get_full_name() or user.get_username()

    def get_credential_name(self, user: AbstractUser) -> str:
        """Get the name for the credential.

        This is used to display the user's name during registration and
        authentication.

        The default implementation calls User.get_username()
        """
        return user.get_username()

    def get_unique_anonymous_user_id(self, user: AbstractUser) -> bytes:
        """Get a unique identifier for the user to use during WebAuthn
        ceremonies. It must be a unique byte sequence no longer than 64 bytes.

        To preserve user privacy, it must not contain any information that may
        lead to the identification of the user. UUIDs may be a good choice for
        this, plain email addresses and usernames are definitely not.

        Clients can use this to identify if they already have a credential
        stored for this user account and act accordingly.

        For more information, see: -
        https://www.w3.org/TR/webauthn-2/#dom-publickeycredentialuserentity-id
        """
        # Because we lack a dedicated field to store random bytes in on the user
        # model, we'll instead resort to hashing the user's primary key as that
        # is unique too and will never change. Since this value doesn't have to
        # be unique across different relying parties, we don't need to salt it.
        # SHA-256 is used because it is fast, commonly used, and produces a
        # 64-byte hash. This is good enough privacy, though not as perfect as
        # random bytes.
        # SECURITY NOTE: The attack vector for de-anonymizing by
        # linking authenticator back to a specific user is small, but still
        # present. If an attacker suspects the authenticator belongs to a
        # specific user, they can obtain the suspected user's primary key and
        # hash it to see if it matches the user ID stored on the authenticator.
        # Random bytes never shared with anyone don't have this issue.
        # TODO: document the need to override this method  and to use random
        # bytes instead.
        return hashlib.sha256(bytes(user.pk)).digest()

    def get_user_entity(self, user: AbstractUser) -> PublicKeyCredentialUserEntity:
        """Get information about the user account a credential is being registered for."""
        return PublicKeyCredentialUserEntity(
            id=self.get_unique_anonymous_user_id(user),
            name=user.get_full_name() or user.get_username(),
            display_name=user.get_full_name() or user.get_username(),
        )

    def get_supported_key_algorithms(self) -> list[COSEAlgorithmIdentifier] | None:
        """Get the key algorithms we support.

        Should return a list of COSE algorithm identifiers that we support. Or
        the special value of `None` to default to py_webauthn's algorithm list.

        For example, to only support ECDSA_SHA_256 and ECDSA_SHA_512, you would
        return [-7, -36] as those are the COSE algorithm identifiers for those
        algorithms.

        For more information, see: -
        https://www.w3.org/TR/webauthn-3/#sctn-alg-identifier -
        https://www.iana.org/assignments/cose/cose.xhtml#algorithms
        """

        raw_algorithms = app_settings.OTP_WEBAUTHN_SUPPORTED_COSE_ALGORITHMS
        if raw_algorithms == "all":
            # Indicates all py_webauthn supported algorithms
            return None

        algorithms = [COSEAlgorithmIdentifier(a) for a in raw_algorithms if a in COSEAlgorithmIdentifier]
        return algorithms

    def get_generate_registration_options_kwargs(self, *, user: AbstractUser) -> dict:
        """Get the keyword arguments to pass to `webauthn.generate_registration_options`."""
        challenge = self.generate_challenge()
        rp = self.get_relying_party()
        user_entity = self.get_user_entity(user)
        attestation_preference = self.get_attestation_conveyance_preference()
        discoverable_credentials = self.get_discoverable_credentials_preference()
        user_verification = UserVerificationRequirement.PREFERRED
        exclude_credentials = WebAuthnCredential.get_credential_descriptors_for_user(user)
        supported_algorithms = self.get_supported_key_algorithms()
        authenticator_selection = AuthenticatorSelectionCriteria(
            user_verification=user_verification, resident_key=discoverable_credentials
        )

        options = {
            "attestation": attestation_preference,
            "authenticator_selection": authenticator_selection,
            "challenge": challenge,
            "exclude_credentials": exclude_credentials,
            "rp_id": rp.id,
            "rp_name": rp.name,
            "user_display_name": user_entity.display_name,
            "user_id": user_entity.id,
            "user_name": user_entity.name,
            # Timeout is in milliseconds, but the setting is in seconds
            "timeout": app_settings.OTP_WEBAUTHN_TIMEOUT_SECONDS * 1000,
        }

        if supported_algorithms:
            options["supported_pub_key_algs"] = supported_algorithms

        return options

    def get_registration_extensions(self) -> dict:
        """Get the extensions to request during registration. Data must be JSON serializable."""
        return {
            # https://developer.mozilla.org/en-US/docs/Web/API/Web_Authentication_API/WebAuthn_extensions#credprops
            # Request that the authenticator tell us if a discoverable
            # credential was created. We keep track of this to determine if
            # passwordless authentication is possible using this credential.
            "credProps": True,
        }

    def get_registration_state(self, creation_options: dict) -> dict:
        """Get the state to store during registration. This state will be used
        to verify the registration later on."""

        return {
            "challenge": creation_options["challenge"],
            "require_user_verification": creation_options["authenticatorSelection"]["userVerification"]
            == UserVerificationRequirement.REQUIRED.value,
        }

    def register_begin(self, user: AbstractUser) -> tuple[dict, dict]:
        """Begin the registration process."""

        kwargs = self.get_generate_registration_options_kwargs(user=user)
        options = generate_registration_options(**kwargs)

        json_string = options_to_json(options)
        # We work with dicts and not JSON strings, so we need to load the JSON
        # string again. Sadly this causes extra overhead but it'll have to do
        # for now.
        data = json.loads(json_string)

        # Manually add the extensions to the options, as the PyWebAuthn library
        # doesn't support this yet.
        extensions = self.get_registration_extensions()
        data["extensions"] = extensions

        state = self.get_registration_state(data)

        return data, state

    def get_allowed_origins(self) -> list[str]:
        """Get the expected origins."""
        origins = app_settings.OTP_WEBAUTHN_ALLOWED_ORIGINS
        return origins

    def register_complete(self, user: AbstractUser, state: dict, data: dict):
        """Complete the registration process."""
        credential = parse_registration_credential_json(data)

        expected_challenge = base64url_to_bytes(state["challenge"])
        allowed_origins = self.get_allowed_origins()
        require_user_verification = state["require_user_verification"]
        expected_rp_id = self.get_relying_party_domain()
        supported_algorithms = self.get_supported_key_algorithms()

        kwargs = {}
        if supported_algorithms:
            kwargs["supported_pub_key_algs"] = supported_algorithms

        response = verify_registration_response(
            credential=credential,
            expected_challenge=expected_challenge,
            expected_rp_id=expected_rp_id,
            expected_origin=allowed_origins,
            require_user_verification=require_user_verification,
            **kwargs,
        )

        device = self.create_credential(user, response, credential, data)
        device.save()
        self.create_attestation(device, response.attestation_object, credential.response.client_data_json)
        return device

    def _check_discoverable(self, original_data: dict) -> Optional[bool]:
        """Check the clientExtensionResults to determine if the credential was
        created as discoverable.

        SECURITY NOTE: clientExtensionResults is not signed by the
        authenticator and is open to tampering by a malicious client. Since we
        are only using it to inform the user and not to make security decisions,
        this is fine.
        """
        if (
            "clientExtensionResults" not in original_data
            or "credProps" not in original_data["clientExtensionResults"]
            or "rk" not in original_data["clientExtensionResults"]["credProps"]
        ):
            return None

        return bool(original_data["clientExtensionResults"]["credProps"]["rk"])

    def create_credential(
        self,
        user: AbstractUser,
        response: VerifiedRegistration,
        parsed_credential: RegistrationCredential,
        original_data: dict,
    ):
        """Save the credential to the database."""
        discoverable = self._check_discoverable(original_data)
        transports = (
            [x.value for x in parsed_credential.response.transports] if parsed_credential.response.transports else []
        )

        # We can't use the backup_eligible flag directly because it's not
        # exposed in the py_webauthn API. We can however infer it from the
        # credential device type. If it's a multi-device credential, it's backup
        # eligible.
        backup_eligible = response.credential_device_type == CredentialDeviceType.MULTI_DEVICE
        backup_state = response.credential_backed_up

        device = WebAuthnCredential(
            user=user,
            aaguid=response.aaguid,
            credential_id=response.credential_id,
            public_key=response.credential_public_key,
            sign_count=response.sign_count,
            transports=transports,
            discoverable=discoverable,
            backup_eligible=backup_eligible,
            backup_state=backup_state,
        )
        # We don't save the device yet, this could result in errors if a custom
        # model has added additional fields. The device will be saved by the
        # caller. This method can be extended to set additional fields on the
        # device before saving.
        return device

    def create_attestation(
        self,
        credential: AbstractWebAuthnCredential,
        attestation_object: bytes,
        client_data_json: bytes,
    ) -> AbstractWebAuthnAttestation:
        """Create an attestation statement for the device."""
        parsed = parse_attestation_object(attestation_object)

        return WebAuthnAttestation.objects.create(
            credential=credential,
            fmt=parsed.fmt,
            data=attestation_object,
            client_data_json=client_data_json,
        )

    def get_authentication_extensions(self) -> dict:
        """Get the extensions to request during authentication. Data must be
        JSON serializable."""
        return {}

    def get_generate_authentication_options_kwargs(
        self, *, user: Optional[AbstractUser] = None, require_user_verification: bool
    ) -> dict:
        """Get the keyword arguments to pass to `webauth.generate_authentication_options`."""

        kwargs = {
            "challenge": generate_challenge(),
            "rp_id": self.get_relying_party_domain(),
            "timeout": app_settings.OTP_WEBAUTHN_TIMEOUT_SECONDS * 1000,
            "user_verification": (
                UserVerificationRequirement.REQUIRED
                if require_user_verification
                else UserVerificationRequirement.DISCOURAGED
            ),
        }

        if user:
            kwargs["allow_credentials"] = WebAuthnCredential.get_credential_descriptors_for_user(user)

        return kwargs

    def get_authentication_state(self, options: dict) -> dict:
        """Get the state to store during authentication. This state will be used
        to verify the authentication later on."""
        return {
            "challenge": options["challenge"],
            "require_user_verification": options["userVerification"] == UserVerificationRequirement.REQUIRED.value,
        }

    def authenticate_begin(
        self,
        user: Optional[AbstractUser] = None,
        require_user_verification: bool = True,
    ):
        """Begin the authentication process."""
        kwargs = self.get_generate_authentication_options_kwargs(
            user=user, require_user_verification=require_user_verification
        )
        options = generate_authentication_options(**kwargs)

        json_string = options_to_json(options)
        # We work with dicts and not JSON strings, so we need to load the JSON
        # string again. Sadly this causes extra overhead but it'll have to do
        # for now.
        data = json.loads(json_string)

        # Manually add the extensions to the options, as the PyWebAuthn library
        # doesn't support this yet.
        extensions = self.get_authentication_extensions()
        data["extensions"] = extensions

        state = self.get_authentication_state(data)
        return data, state

    def authenticate_complete(self, user: Optional[AbstractUser], state: dict, data: dict):
        """Complete the authentication process."""

        credential = parse_authentication_credential_json(data)

        try:
            device = WebAuthnCredential.get_by_credential_id(credential.raw_id)
        except WebAuthnCredential.DoesNotExist:
            raise exceptions.CredentialNotFound()

        expected_challenge = base64url_to_bytes(state["challenge"])
        expected_origins = self.get_allowed_origins()
        require_user_verification = state["require_user_verification"]
        expected_rp_id = self.get_relying_party_domain()
        supported_algorithms = self.get_supported_key_algorithms()

        kwargs = {}
        if supported_algorithms:
            kwargs["supported_algorithms"] = supported_algorithms

        response = verify_authentication_response(
            credential=credential,
            credential_current_sign_count=device.sign_count,
            credential_public_key=device.public_key,
            expected_challenge=expected_challenge,
            expected_rp_id=expected_rp_id,
            expected_origin=expected_origins,
            require_user_verification=require_user_verification,
            **kwargs,
        )

        device.sign_count = response.new_sign_count
        device.backup_state = response.credential_backed_up
        device.set_last_used_timestamp(commit=False)
        device.save(update_fields=["sign_count", "last_used_at", "backup_state"])

        return device
