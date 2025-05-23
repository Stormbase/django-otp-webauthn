.. _views:

Views
=====

Django OTP WebAuthn provides the following built-in API views:

BeginCredentialRegistrationView
-------------------------------

``BeginCredentialRegistrationView`` is responsible for sending the challenge and options for credential registration back to the client. It also sets up the state in the session and requires the user to be logged in.

CompleteCredentialRegistrationView
----------------------------------

``CompleteCredentialRegistrationView`` receives data from the client about the created credential, validates it, and stores it in the database.

If validation fails, it raises a Django REST Framework exception to notify the frontend of the error. The frontend then informs the browser that the registration was unsuccessful, prompting the removal of the partially registered :term:`passkey <passkey/discoverable credential>`.

BeginCredentialAuthenticationView
---------------------------------

``BeginCredentialAuthenticationView`` is responsible for sending the challenge and options to use during authentication back to the client. It also sets up the state in the session.

If the user is already logged in, such as during 2FA verification, it sets the ``allowCredentials`` option. This ensures that the browser prompt shows only the end-user credentials registered to the logged-in user.

CompleteCredentialAuthenticationView
------------------------------------

``CompleteCredentialAuthenticationView`` receives data from the client after the user approves the login prompt. It then looks up the correct ``WebAuthnCredential`` object in the database using the received ``credential_id``. The signature is validated using the :term:`public key` stored on the WebAuthnCredential instance.

The system also checks other requirements, such as whether the :term:`authenticator` performed user verification by prompting for a PIN, password, or fingerprint, if requested.

Finally, the system logs in the user associated with the ``WebAuthnCredential`` and marks them as having passed 2FA authentication.

WellKnownWebAuthnView
---------------------

``WellKnownWebAuthnView`` supports WebAuthn across related origins.

The view returns a JSON response containing the list of related origins configured in the ``OTP_WEBAUTHN_RP_RELATED_ORIGINS`` setting. This allows :term:`WebAuthn credentials <WebAuthn credential>` to work across multiple domains that share the same :term:`relying party`.

The view permits public access, doesn't require authentication, and accepts only GET requests. Also, Responses are cached for 10 minutes.

You can Configure this view at the ``/.well-known/webauthn`` URL. Define the ``OTP_WEBAUTHN_RP_RELATED_ORIGINS`` setting as a list of secure origins.

The view accepts only origins that use ``https`` or ``http://localhost`` for local development.
