.. _howto-identify-passkeys:

How-to: identify passkeys
=========================

.. versionadded:: v0.11.0

.. note::
    This page is a **how to guide**. Maybe you are looking for the :ref:`Identify passkeys reference guide<ref_identify_passkeys>` instead?

Django OTP WebAuthn ships with a ``django.contrib.identify`` module which helps
you identify the :term:`authenticator` that created the Passkey. For example, it can identify Apple Passwords, YubiKey, and Android. This is useful context to give your users when
presenting them with a list of their registered Passkeys.

Before you use this module, note the following:

TLDR;

What to know before you use this module
---------------------------------------

- This module gives you *authenticator icons* and *authenticator names* for the passkeys your users register, so you can display them in your app's interface.
- You can't identify every passkey. Identification works on a best-effort basis.
- Don't use this module for security decisions, such as rejecting passkeys that aren't on an approved list.
- The passkey identifier database comes from `python-identify-passkey <https://github.com/Stormbase/python-identify-passkey>`_. Update this library regularly to get the latest identifiers.
- The `python-identify-passkey <https://github.com/Stormbase/python-identify-passkey>`_ library draws its data from the `FIDO MDS registry <https://fidoalliance.org/metadata/>`_ of FIDO-certified authenticators, plus community contributions.

Install module
--------------

To install the ``django.contrib.identify`` module, install ``django_otp_webauthn`` with the ``identify`` extra:

.. code-block:: console

    pip install django_otp_webauthn[identify]

This will install the required `python-identify-passkey
<https://github.com/Stormbase/python-identify-passkey>`_ library, which
contains the most up-to-date list of passkey identifiers.

Configure settings
^^^^^^^^^^^^^^^^^^

Next, add ``django_otp_webauthn.contrib.identify`` to your :setting:`INSTALLED_APPS`:

.. code-block:: python

    INSTALLED_APPS = [
        ...
        "django_otp_webauthn",
        "django_otp_webauthn.contrib.identify",
    ]

And add :class:`django_otp_webauthn.contrib.identify.PasskeyIconsFinder`, to your
:setting:`STATICFILES_FINDERS`.

If you don't have a :setting:`STATICFILES_FINDERS` setting,
then add it as follows:

.. code-block:: python

    STATICFILES_FINDERS = [
        "django.contrib.staticfiles.finders.FileSystemFinder",  # part of django defaults
        "django.contrib.staticfiles.finders.AppDirectoriesFinder",  # part of django defaults
        "django_otp_webauthn.contrib.identify.PasskeyIconsFinder",
    ]

This will allow you to use any of the icons shipped inside the
``python-identify-passkey`` library, for example the Apple Passkey icon.

Usage examples
--------------

Now that you have installed and configured the
``django_otp_webauthn.contrib.identify`` module, you can use it to identify
passkeys in your application. For example, you could use the inferred name of
the authenticator as fallback name for a passkey in your user interface, or show
the icon of the authenticator next to the passkey name.

``AbstractWebAuthnCredential.identify``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can use the :meth:`django_otp_webauthn.models.AbstractWebAuthnCredential.identify` method to identify a credential instance.

When identifiable, this gives you a :class:`django_otp_webauthn.contrib.identify.PasskeyDescriptor` object, which contains the name of the authenticator and a light and dark icon.

.. code-block:: python

    from django_otp_webauthn.models import WebAuthnCredential

    credential = WebAuthnCredential.objects.get(pk=1)
    passkey_descriptor = credential.identify()

    if passkey_descriptor:
        print(repr(passkey_descriptor))  # PasskeyDescriptor(name='Apple Passwords', aaguid='fbfc3007-154e-4ecc-8c0b-6e020557d7bd')
        print(repr(passkey_descriptor.icon_light)) # PasskeyIcon(theme='light', mime='image/svg+xml', path='/path/to/svg/file.svg')
        print(repr(passkey_descriptor.icon_dark)) # PasskeyIcon(theme='dark', mime='image/svg+xml', path='/path/to/svg/file.svg')


``AbstractWebAuthnCredential.inferred_name``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Credentials have an :attr:`django_otp_webauthn.models.AbstractWebAuthnCredential.inferred_name` property that returns the name of the authenticator when it can be identified, or ``None`` otherwise.

.. code-block:: python

    from django_otp_webauthn.models import WebAuthnCredential

    credential = WebAuthnCredential.objects.get(pk=1)
    print(credential.inferred_name)  # Apple Passwords


Identify a Passkey without a credential instance
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use the :func:`django_otp_webauthn.contrib.identify.identify_passkey` function to identify a Passkey directly by its ``AAGUID``.

.. code-block:: python

    from django_otp_webauthn.contrib.identify import identify_passkey

    aaguid = "fbfc3007-154e-4ecc-8c0b-6e020557d7bd"  # Apple Passwords AAGUID
    passkey_descriptor = identify_passkey(aaguid)

    if passkey_descriptor:
        print(repr(passkey_descriptor))  # PasskeyDescriptor(name='Apple Passwords', aaguid='fbfc3007-154e-4ecc-8c0b-6e020557d7bd')
        print(repr(passkey_descriptor.icon_light)) # PasskeyIcon(theme='light', mime='image/svg+xml', path='/path/to/svg/file.svg')
        print(repr(passkey_descriptor.icon_dark)) # PasskeyIcon(theme='dark', mime='image/svg+xml', path='/path/to/svg/file.svg')
