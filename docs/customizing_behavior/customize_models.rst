.. _customize-models:

Customize models
==================

Django OTP WebAuthn provides the following base models for credentials and attestations:

* ``AbstractWebAuthnCredential``
* ``AbstractWebAuthnAttestation``

These models have all the necessary fields and methods. If the base models don't suit your needs, you can create custom models. However, if you're using a custom model for credentials, you must also use a custom model for your attestation.

For more information, see the reference docs on :ref:`Models <models>`.

Create a custom model
---------------------

To create custom models, define a credential model that inherits from ``AbstractWebAuthnCredential``. Then, define an attestation model inheriting from ``AbstractWebAuthnAttestation``. Override the credential field in the attestation model to reference the custom credential model with a OneToOneField:

.. code-block:: py

    from django.db import models
    from django_otp_webauthn.models import AbstractWebAuthnAttestation, AbstractWebAuthnCredential

    class MyCredential(AbstractWebAuthnCredential):
        pass

    class MyAttestation(AbstractWebAuthnAttestation):
        credential = models.OneToOneField(
            MyCredential,
            on_delete=models.CASCADE,
            related_name="attestation",
            editable=False
        )

You can also override the attestation model without modifying the default credential model. However, you must set a ``related_name`` for the credential field that differs from ``attestation`` to avoid conflicts with the default model’s ``related_name`` property:

.. code-block:: py

    from django.db import models
    from django_otp_webauthn.models import AbstractWebAuthnAttestation

    class MyAttestation(AbstractWebAuthnAttestation):
        credential=models.OneToOneField("otp_webauthn.    WebAuthnCredential", on_delete=models.CASCADE,     related_name="swapped_attestation", editable=False)

Handle database index name length errors
----------------------------------------

The ``AbstractWebAuthnCredential`` model automatically generates an index name that includes the concrete model’s name, with ``_sha256_idx`` appended. If the model name is more than 30 characters, the auto-generated index name may exceed your database's maximum identifier length. This can result in errors during migrations, such as:

.. code-block:: console

    SystemCheckError: System check identified some issues:

    ERRORS:
    <app_label>.<ModelName>: (models.E034) The index name '<mycredentialmodelwithalongname>_sha256_idx' cannot be longer than 30 characters.

If you encounter such an error, you can override the index in your credential model to ensure the index name is within the appropriate length limit like this:

.. code-block:: py

    class MyCredentialModelWithALongName(AbstractWebAuthnCredential):

    class Meta:
        indexes = [
            models.Index(fields=["credential_id_sha256"], name="mycredential_id_sha256_idx"),
        ]
