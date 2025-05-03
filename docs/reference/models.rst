.. _models:

Models
======

Django OTP WebAuthn comes with two abstract models that you can customize. Each abstract model has a concrete version that you can use out of the box:

* ``AbstractWebAuthnCredential``

* ``AbstractWebAuthnAttestation``

Django OTP WebAuthn also includes the ``WebAuthnUserHandle`` model, which stores persistent user identifiers and is not intended to be customized.

.. _abstractwebauthncredential:

AbstractWebAuthnCredential
--------------------------

``AbstractWebAuthnCredential`` subclasses ``django_otp.models.Device``. It stores the :term:`public key` part of a credential.

AbstractWebAuthnAttestation
---------------------------

``AbstractWebAuthnAttestation`` stores :term:`attestations <attestation>` made when you register a credential.

.. attention::
   Support for attestations isn't actively implemented, but might be extended in the future.

In the context of :term:`Web Authentication`, an attestation provides verifiable evidence of an :term:`authenticator's <authenticator>` origin when creating a credential. For more details, refer to the definitions of `attestation <https://www.w3.org/TR/webauthn-3/#attestation>`_ and `authenticator <https://www.w3.org/TR/webauthn-2/#authenticator>`_ in the specification.

You can use attestation to check if the credential was created by a genuine implementation of the Web Authentication standard. This is important, as a significant level of trust is placed on the client-side implementation of the standard.

WebAuthnUserHandle
------------------

``WebAuthnUserHandle`` stores a persistent identifier known as a user handle for each user. :term:`WebAuthn` authenticators use this user handle to determine if a :term:`credential <WebAuthn credential>` already exists for a user.

Each user handle is 64 random bytes stored as a hex string. This format ensures compatibility across databases and permits indexing. Every user has one user handle. The model links the user handle to the user using a ``one-to-one`` relationship.

You should treat the user handle's value as sensitive information by not exposing it to anyone except the rightful owner.

``WebAuthnUserHandle`` provides the following methods for working with user handles:

* ``get_handle_for_user``: Get or create the handle for the given user.

* ``get_user_by_handle``: Look up the user associated with a given handle as bytes. It returns ``None`` if no user is found.

For more information, see the `WebAuthn specification on user handle privacy <https://www.w3.org/TR/webauthn-3/#sctn-user-handle-privacy>`_.
