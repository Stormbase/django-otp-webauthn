.. _customize-helper-class:

Customize helper class
======================

The :term:`WebAuthn` helper class acts as the bridge between views, models, and ``py_webauthn``. You can customize it to customize the behavior of WebAuthn in your Django application. For example, if you add additional fields to the credential model, you may want to override the ``create_credential`` method to populate these fields.

To customize the WebAuthn helper class, follow these steps:

1. Start by subclassing ``django_otp_webauthn.helpers.WebAuthnHelper`` and override its methods as needed to implement your custom logic. For example, you can override the ``create_credential`` method by creating a ``webauthn_helpers.py`` file in your Django app:

.. code-block:: py

    from django_otp_webauthn.helpers import WebAuthnHelper

    class CustomWebAuthnHelper(WebAuthnHelper):
        def create_credential(self, *args, **kwargs):
            # Override methods here
            credential = super().create_credential(*args, **kwargs)
            credential.my_custom_field = "my_custom_value"

            # The caller is responsible for saving the credential
            return credential

2. Replace the default helper class with your custom class by updating the ``OTP_WEBAUTHN_HELPER_CLASS`` setting in your Django settings file. Set it to the dotted path of your custom class:

.. code-block:: py

    OTP_WEBAUTHN_HELPER_CLASS = "<your-app>.webauthn_helpers.CustomWebAuthnHelper"

For further customization, modify the WebAuthn configuration options passed to the browser. For more information, see the reference docs on :ref:`Helper <helper>`.
