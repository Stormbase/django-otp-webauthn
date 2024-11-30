import enum
from dataclasses import dataclass


# Matches StatusEnum in types.ts
class StatusEnum(enum.StrEnum):
    UNKNOWN_ERROR = "unknown-error"
    STATE_ERROR = "state-error"
    SECURITY_ERROR = "security-error"
    GET_OPTIONS_FAILED = ("get-options-failed",)
    ABORTED = "aborted"
    NOT_ALLOWED_OR_ABORTED = "not-allowed-or-aborted"
    SERVER_ERROR = "server-error"
    SUCCESS = "success"
    BUSY = "busy"


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
