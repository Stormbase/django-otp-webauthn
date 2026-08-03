.. _ref_configuration:


Configuration
=============

This reference page lists all the available configuration options and what
effect they have. Configure these options in your Django settings file, for example:

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
