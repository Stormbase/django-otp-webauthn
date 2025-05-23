Configure for related origins
=============================

You can use ``WellKnownWebAuthnView`` to configure your application to use the same :term:`WebAuthn credentials <WebAuthn credential>` across multiple domains. For example, if your main application runs on ``https://example.com`` and you have a localized version on ``https://example.co.uk`` and ``https://example.de``.

Set up the URL
--------------

Modify your ``<project>/urls.py`` file and add the required URL configuration:

.. code-block:: py
    
    from django.urls import path
    from django_otp_webauthn.views import WellKnownWebAuthnView

    urlpatterns = [
        ...
        path(".well-known/webauthn", WellKnownWebAuthnView.as_view()),
    ]

Add related origins to your Django settings
-------------------------------------------

Now in your ``<project>/settings.py`` file, add your related origins to ``OTP_WEBAUTHN_RP_RELATED_ORIGINS``:

.. code-block:: py
    
    OTP_WEBAUTHN_RP_RELATED_ORIGINS = [
        "https://example.com",
        "https://example.co.uk",
        "https://example.de",
        "https://app.example.com"
    ]

The related origins must use ``HTTPS``, except for localhost origins which can use ``HTTP`` for local development.

For more information, see the reference docs on :ref:`WellKnownWebAuthnView <wellknownwebauthnview>`.
