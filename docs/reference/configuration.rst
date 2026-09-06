:og:title: Django OTP WebAuthn configuration reference
:og:description: Setting and configuration options in Django OTP WebAuthn to customize the behaviors of WebAuthn, including attestation conveyance preference, relying party ID, and relying party name.
:og:image:alt: Setting and configuration options in Django OTP WebAuthn to customize the behaviors of WebAuthn, including attestation conveyance preference, relying party ID, and relying party name.

.. meta::
    :title: Django OTP WebAuthn configuration reference
    :description: Setting and configuration options in Django OTP WebAuthn to customize the behaviors of WebAuthn, including attestation conveyance preference, relying party ID, and relying party name.

.. _ref_configuration:

Reference: configuration
========================

This reference page lists the available configuration options and describes what
each option controls. Configure these options in your Django
`<project>/settings.py`` file. For example:

.. code-block:: python

    # settings.py
    OTP_WEBAUTHN_ATTESTATION_CONVEYANCE_PREFERENCE = "none"
    OTP_WEBAUTHN_RP_ID = "my-django-app.com"
    OTP_WEBAUTHN_RP_NAME = "My Django App"

.. automodule:: django_otp_webauthn.settings
    :noindex:

    .. autoclass:: django_otp_webauthn.settings.AppSettings
        :exclude-members: __init__, __new__
        :members:
        :member-order: bysource
