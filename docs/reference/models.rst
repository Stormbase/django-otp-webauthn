.. _models:

Models
======

Django OTP WebAuthn comes with two abstract classes that you can subclass to create your own models. Each abstract class has a concrete version that you can use out of the box.

AbstractWebAuthnCredential
--------------------------

``AbstractWebAuthnCredential`` subclasses ``django_otp.models.Device``. It stores the :term:`public key` part of a credential.

AbstractWebAuthnAttestation
---------------------------

``AbstractWebAuthnAttestation`` stores attestations made when you register a credential.

.. attention::
   Support for attestations isn't actively implemented, but might be extended in the future.

In the context of :term:`Web Authentication`, an attestation provides verifiable evidence of an :term:`authenticator's <authenticator>` origin when creating a credential. For more details, refer to the definitions of `attestation <https://www.w3.org/TR/webauthn-3/#attestation>`_ and `authenticator <https://www.w3.org/TR/webauthn-2/#authenticator>`_ in the specification.

You can use attestation to check if the credential was created by a genuine implementation of the Web Authentication standard. This is important, as a significant level of trust is placed on the client-side implementation of the standard.
