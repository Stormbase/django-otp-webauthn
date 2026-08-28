How-to guides
=============

This section provides step-by-step guides to help you implement key features of Django OTP WebAuthn.

Here are what you will find in this section:

.. grid:: 1 1 2 2
   :gutter: 3
   :margin: 0

   .. grid-item-card:: :ref:`Sharing passkeys between domains <configure_related_origins>`

       Learn how to configure WebAuthn to work across multiple domains. For example, if your main application runs on ``https://example.com`` and you have a localized version on ``https://example.co.uk``.

   .. grid-item-card:: :ref:`Identify passkeys <howto-identify-passkeys>`

       Learn how to identify the authenticator that created a Passkey, for example Apple Passwords, Yubikey, Android etc. This is useful context to give your users when presenting them with a list of their registered Passkeys.

   .. grid-item-card:: :ref:`Customize views <customize-views>`

       Learn how to subclass Django OTP WebAuthn's built-in views to customize registration and authentication behavior. For example, adding restrictions or logging mechanisms.

   .. grid-item-card:: :ref:`Customize helper class <customize-helper-class>`

       Learn how to customize the behavior of :term:`WebAuthn` in your Django application. For example, if you want to add additional fields to the credential model.

   .. grid-item-card:: :ref:`Customize models <customize-models>`

       Learn how to create custom Django OTP WebAuthn models if the base models don't suit your needs.

   .. grid-item-card:: :ref:`Keep passkeys up-to-date with changing user details <keep_passkeys_in_sync>`

       Learn how to keep Passkey user details saved in users' browsers up-to-date when details like email or username change.

.. toctree::
    :maxdepth: 2
    :hidden:

    Share passkeys between domains <configure_related_origins.rst>
    Identify passkeys <identify_passkeys.rst>
    Customize views <customize_views.rst>
    Customize helper class <customize_helper_class.rst>
    Customize models <customize_models.rst>
    Keep passkeys up-to-date with changing user details <keep_passkeys_in_sync.rst>
