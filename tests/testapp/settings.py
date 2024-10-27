# Use this settings file to run manage.py commands in the testapp.
#
# Example:
#  $ DJANGO_SETTINGS_MODULE=tests.testapp.settings python manage.py

from sandbox.settings import *  # noqa

INSTALLED_APPS += [  # noqa: F405
    "tests.testapp",
]

OTP_WEBAUTHN_RP_ID = "example.com"
OTP_WEBAUTHN_RP_NAME = "Example Corp."
OTP_WEBAUTHN_CREDENTIAL_MODEL = "testapp.CustomCredential"
OTP_WEBAUTHN_ATTESTATION_MODEL = "testapp.CustomAttestation"
