.. This file intentionally avoids using `.. contents::` directive for table of contents
.. because Furo's styling conflicts with manual TOC implementations. Instead:
.. - Furo automatically generates a sidebar TOC (no action needed)
.. - For in-content navigation, use manual section links with `:ref:` labels
.. See https://pradyunsg.me/furo/customisation/sidebar/#table-of-contents

Frequently asked questions
==========================


- :ref:`replace-passwords`

- :ref:`manage-passkeys`

- :ref:`yubikey-registration`

.. _replace-passwords:

Can this package fully replace passwords in my application?
-----------------------------------------------------------

Django OTP WebAuthn isn’t designed to fully replace passwords in your application. Instead, it adds :term:`WebAuthn` functionality to an existing application, complementing other authentication mechanisms. This is why it’s implemented as a plugin for the ``django-otp`` framework.

If you need a fully passwordless solution, consider using a different package that better suits your requirements.

.. _manage-passkeys:

Can I manage and name passkeys after registration?
--------------------------------------------------

With the exception of the Django admin site, no user-visible interface is provided for managing registered :term:`passkeys <passkey/discoverable credential>`. This is intentional, as we believe such an interface should be site specific, `similar to django-otp <https://django-otp-official.readthedocs.io/en/stable/auth.html#managing-devices>`_. So it’s up to you to implement as you see fit.

The same applies to naming a passkey after registration.

.. _yubikey-registration:

Why can't I register my YubiKey or security key when passwordless login is turned on?
-------------------------------------------------------------------------------------

If you’re trying to use a ``YubiKey`` or a similar security key with passwordless login enabled, you may run into registration issues. This is because when passwordless login is enabled, only certain types of devices can be registered. This helps prevent confusion when a device doesn’t work during authentication.

In this case, the credential created isn’t technically a passkey. It's what the `Web Authentication specification <https://www.w3.org/TR/webauthn-3/>`_ calls a `server-side credential <https://www.w3.org/TR/webauthn-3/#server-side-credential>`_. Unlike a true passkey, where the :term:`private key` is stored on the device, the private key here is encrypted and stored in the :term:`credential ID` field on the server. This approach is necessary because some security keys have limited memory and can only store a small number of credentials.

So to use a security key for passwordless login, the user must provide at least a username. This allows the system to look up the credentials associated with that account. However, this process requires returning all credential IDs to an unauthenticated and untrusted site visitor. This complicates the authentication process and risks leaking information about the user and their registered passkeys.

Due to these complexities, we decided not to support this functionality.

However, it’s possible to register and use these security keys when passwordless login functionality is disabled. When used as a :term:`second-factor authentication`, the user is already partially authenticated so it’s much more straightforward to return credential IDs.

You can still register and use these security keys when passwordless login is disabled. When used as a second-factor authentication method, the user is already partially authenticated, making it easier to return credential IDs securely.

If you want more details, this restriction is done by setting the residentKey authenticator selection criteria to required. For more information, see `authenticatorSelection.residentKey in the Web Authentication specification <https://www.w3.org/TR/webauthn-2/#dom-authenticatorselectioncriteria-residentkey>`_.
