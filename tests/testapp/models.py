from django.db import models

from django_otp_webauthn.models import (
    AbstractWebAuthnAttestation,
    AbstractWebAuthnCredential,
)


class CustomCredential(AbstractWebAuthnCredential):
    pass


class CustomAttestation(AbstractWebAuthnAttestation):
    credential = models.OneToOneField(
        to="testapp.CustomCredential",
        on_delete=models.CASCADE,
        related_name="attestation",
        verbose_name="credential",
        editable=False,
    )
