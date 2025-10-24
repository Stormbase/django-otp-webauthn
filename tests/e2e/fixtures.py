import enum
import hashlib
from base64 import b64encode
from dataclasses import dataclass

from webauthn.helpers import base64url_to_bytes

from django_otp_webauthn.models import AbstractWebAuthnCredential


# Matches StatusEnum in types.ts
class StatusEnum(enum.StrEnum):
    UNKNOWN_ERROR = "unknown-error"
    STATE_ERROR = "state-error"
    SECURITY_ERROR = "security-error"
    GET_OPTIONS_FAILED = "get-options-failed"
    ABORTED = "aborted"
    NOT_ALLOWED_OR_ABORTED = "not-allowed-or-aborted"
    SERVER_ERROR = "server-error"
    SUCCESS = "success"
    BUSY = "busy"


KNOWN_INTERNAL_PRIVATE_KEY = "MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQggJbdYAOvm/MOu47dJ034ggl4Miqx1WGrzxiX+A4WwnehRANCAARCCxh40Cwk4o3erCjJHjFIZkYc7BNAt3+UD5c6Y0I/V9ILewFU2lG388izmQMkrmMFFuZ4GuFTtphFSBl3XLdq"
KNOWN_INTERNAL_PUBLIC_KEY = "a5010203262001215820420b1878d02c24e28ddeac28c91e314866461cec1340b77f940f973a63423f57225820d20b7b0154da51b7f3c8b3990324ae630516e6781ae153b698454819775cb76a"

KNOWN_U2F_CREDENTIAL_ID = "OuVTUj2NPvclahvg2GJZF3cLnQtnX8YhVGMPtkojEbU="
KNOWN_U2F_PRIVATE_KEY = "MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgCMwjENBovsDoqXgR7K0QPBx7aIgNzpK3RYudN29uMFGhRANCAARIawncyJcuQBHRViZ5mNGWq6R4CnMIjEvcOfQQ1zqnmV0CGcVykWlPY2aqsWF1bN4W/+7zEkt0a67JsWFmh15N"
KNOWN_U2F_PUBLIC_KEY = "a5010203262001215820486b09dcc8972e4011d156267998d196aba4780a73088c4bdc39f410d73aa7992258205d0219c57291694f6366aab161756cde16ffeef3124b746baec9b16166875e4d"


@dataclass(frozen=True)
class VirtualCredential:
    credential_id: str
    is_resident_credential: bool
    user_handle: str
    private_key: str
    backup_eligible: bool
    backup_state: bool
    sign_count: int = 1
    rp_id: str = "localhost"

    def as_cdp_options(self) -> dict:
        return {
            "credentialId": self.credential_id,
            "userHandle": self.user_handle,
            "isResidentCredential": self.is_resident_credential,
            "privateKey": self.private_key,
            "signCount": self.sign_count,
            "backupEligible": self.backup_eligible,
            "backupState": self.backup_state,
            "rpId": self.rp_id,
        }

    @classmethod
    def from_model(
        cls, credential: AbstractWebAuthnCredential, require_u2f: bool = False
    ):
        if require_u2f:
            # U2F credentials are bit more involved, use values known to work
            credential_id = KNOWN_U2F_CREDENTIAL_ID
            private_key = KNOWN_U2F_PRIVATE_KEY
            public_key = KNOWN_U2F_PUBLIC_KEY
        else:
            credential_id = b64encode(credential.credential_id).decode("utf-8")
            private_key = KNOWN_INTERNAL_PRIVATE_KEY
            public_key = KNOWN_INTERNAL_PUBLIC_KEY

        browser_credential = cls(
            credential_id=credential_id,
            user_handle=b64encode(
                hashlib.sha256(bytes(credential.user.pk)).digest()
            ).decode("utf-8"),
            is_resident_credential=bool(
                credential.discoverable
            ),  # If null (unknown), assume false
            sign_count=credential.sign_count,
            backup_eligible=bool(credential.backup_eligible),
            backup_state=bool(credential.backup_state),
            private_key=private_key,
        )
        # We need to match what the browser sends us, update this credential to match
        credential.public_key = bytes.fromhex(public_key)
        credential.credential_id = base64url_to_bytes(credential_id)
        # Clear hash, have it be recalculated
        credential.credential_id_sha256 = None
        credential.save()
        return browser_credential


@dataclass(frozen=True)
class VirtualAuthenticator:
    transport: str
    protocol: str
    has_resident_key: bool
    has_user_verification: bool
    is_user_verified: bool
    default_backup_eligibility: bool
    default_backup_state: bool
    automatic_presence_simulation: bool

    def as_cdp_options(self) -> dict:
        return {
            "transport": self.transport,
            "protocol": self.protocol,
            "hasResidentKey": self.has_resident_key,
            "hasUserVerification": self.has_user_verification,
            "isUserVerified": self.is_user_verified,
            "defaultBackupEligibility": self.default_backup_eligibility,
            "defaultBackupState": self.default_backup_state,
            "automaticPresenceSimulation": self.automatic_presence_simulation,
        }

    @classmethod
    def internal(cls):
        return cls(
            transport="internal",
            protocol="ctap2",
            has_resident_key=True,
            has_user_verification=True,
            is_user_verified=True,
            default_backup_eligibility=True,
            default_backup_state=False,
            automatic_presence_simulation=True,
        )

    @classmethod
    def u2f(cls):
        return cls(
            transport="usb",
            protocol="u2f",
            has_resident_key=False,
            has_user_verification=False,
            is_user_verified=False,
            default_backup_eligibility=False,
            default_backup_state=False,
            automatic_presence_simulation=True,
        )
