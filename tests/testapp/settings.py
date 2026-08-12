# Use this settings file to run manage.py commands in the testapp.
#
# Example:
#  $ DJANGO_SETTINGS_MODULE=tests.testapp.settings python manage.py

from sandbox.settings import *  # noqa: F403
from sandbox.settings import INSTALLED_APPS, STATICFILES_FINDERS

INSTALLED_APPS += [
    "tests.testapp",
]

# Remove the identify app and PasskeyIconsFinder from STATICFILES_FINDERS for testing purposes
INSTALLED_APPS = tuple(
    app for app in INSTALLED_APPS if app != "django_otp_webauthn.contrib.identify"
)
STATICFILES_FINDERS = tuple(
    finder
    for finder in STATICFILES_FINDERS
    if finder != "django_otp_webauthn.contrib.identify.PasskeyIconsFinder"
)

OTP_WEBAUTHN_RP_ID = "example.com"
OTP_WEBAUTHN_RP_NAME = "Example Corp."
OTP_WEBAUTHN_CREDENTIAL_MODEL = "testapp.CustomCredential"
OTP_WEBAUTHN_ATTESTATION_MODEL = "testapp.CustomAttestation"
