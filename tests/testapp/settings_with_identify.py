from sandbox.settings import *  # noqa: F403
from sandbox.settings import INSTALLED_APPS, STATICFILES_FINDERS

if "django_otp_webauthn.contrib.identify" not in INSTALLED_APPS:
    INSTALLED_APPS += [
        "django_otp_webauthn.contrib.identify",
    ]
STATICFILES_FINDERS += [
    "django_otp_webauthn.contrib.identify.PasskeyIconsFinder",
]
OTP_WEBAUTHN_ATTESTATION_CONVEYANCE_PREFERENCE = "direct"
