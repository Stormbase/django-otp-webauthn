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

.. _wellknownwebauthnview:

WellKnownWebAuthnView
---------------------

``WellKnownWebAuthnView`` supports :term:`WebAuthn` across related origins. The view permits public access, doesn't require authentication, and accepts only ``GET`` requests. It also accepts origins that use ``https`` or ``http://localhost`` for local development, and caches responses for 10 minutes.

Use cases
~~~~~~~~~

Two use cases necessitate allowing requests from related origins.

The first use case is deployments that use different :term:`country code top-level domains (ccTLD) <country code top-level domain (ccTLD)>` worldwide. For example, a grocery website might use ``https://grocery.com`` for users in the United States, ``https://grocery.co.uk`` for the United Kingdom, and ``https://grocery.de`` for Germany.

The second use case is for organizations that offer additional services with different or extended branding and share the same accounts. For example, a grocery website may have a website for taking orders from buyers and a separate website for tracking delivery.

How it works
~~~~~~~~~~~~

``WellKnownWebAuthnView`` works by allowing a :term:`relying party` to provide a list of valid origins for a given :term:`relying party ID (rpID)`.

During a WebAuthn operation, the browser checks whether the current origin matches the rpID. If the origin and rpID differ, and the browser supports related origin requests, the browser queries the ``/.well-known/webauthn`` endpoint hosted at the rpID. The server responds with a JSON document that includes a top-level ``origins`` key, with a list of related origins as its value. The browser verifies the list and continues with authentication if the current origin is included.

The browser processes this list using **labels**. A label refers to the part of the domain directly preceding the top-level domain. For example, ``grocery`` is the label for domains like ``https://grocery.com``, ``https://grocery.co.uk``, and ``https://grocery.de``. This grouping allows browsers to support origin lists efficiently without processing excessive unique entries.

Client implementations shouldn't support more than five labels. So if the list contains 30 domains that all share the label ``grocery``, the browser counts these as a single unique label.

Configuration
~~~~~~~~~~~~~

To support related origins, define the list of allowed origins in the ``OTP_WEBAUTHN_RP_RELATED_ORIGINS`` setting. Each origin must use ``https``, except for ``http://localhost`` during development.

Also, a JSON document must be hosted at the WebAuthn well-known path for the rpID, ``/.well-known/webauthn``. For example, if the rpID is ``grocery.com``, the full URL would be ``https://grocery.com/.well-known/webauthn``. The server must also respond with a content type of ``application/json``. The JSON response must contain the list of related origins configured in ``OTP_WEBAUTHN_RP_RELATED_ORIGINS`` in the ``<project>/settings.py`` file.

Here is an example configuration in the ``<project>/settings.py`` file:

.. code-block:: py

    OTP_WEBAUTHN_RP_RELATED_ORIGINS = [
        "https://grocery.com",
        "https://grocery.co.uk",
        "https://grocery.de",
    ]

The JSON response will look like this:

.. code-block:: json

    {
        "origins": [
            "https://grocery.com",
            "https://grocery.co.uk",
            "https://grocery.de",
        ]
    }

Choosing rpID
~~~~~~~~~~~~~

The most important decision when configuring your application for related origins is choosing a primary rpID. All related origins must use the primary rpID for authentication. You should select the domain most closely tied to your brand, usually the ``.com`` domain.

Existing deployments that already use multiple rpIDs face different challenges. The system must maintain backward compatibility while implementing the related origins feature. Users with passkeys tied to the local rpID can continue normal operations, while those with credentials from other origins require additional steps. The solution requires each existing rpID to serve its well-known WebAuthn document listing all authorized origins. The backend must track which rpID created each passkey through explicit metadata or derived information. The login interface must handle cases where automatic recognition fails by implementing username-based lookup flows that redirect users to the correct authentication endpoint.

Browser compatibility
~~~~~~~~~~~~~~~~~~~~~

All deployments must account for browser compatibility since not all browsers support related origin requests. The system should detect browser capabilities and provide fallback authentication methods when needed. For the list of supported browsers, see `Matrix <https://passkeys.dev/device-support/#matrix>`_.
