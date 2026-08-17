.. _howto-identifying-passkeys:

How to: Identify Passkeys
=========================

.. versionadded:: v0.11.0

.. note::
    This page is a **how to guide**. Maybe you are looking for the :ref:`Identifying Passkeys reference guide<ref_identifying_passkeys>` instead?

Django OTP WebAuthn ships with a ``django.contrib.identify`` module which helps
you identify the :term:`authenticator` that created the Passkey, for example Apple
Passwords, Yubikey, Android etc. This is useful context to give your users when
presenting them with a list of their registered Passkeys.

Before using this module
------------------------

TLDR;

1. This module is meant to help you enrich your app's user interface with *authenticator icons* and *authenticator names* of the Passkeys that your users have registered.
2. Not all Passkeys can be identified. This is on best-effort basis, improvements welcome.
3. This is not meant to be used for security purposes, such as rejecting Passkeys not on some approved list.
4. The database of Passkey identifiers comes from `python-identify-passkey <https://github.com/Stormbase/python-identify-passkey>`_. You should regularly update this library to get the latest list of Passkey identifiers.
5. The `python-identify-passkey
   <https://github.com/Stormbase/python-identify-passkey>`_ library's data is derived
   from `FIDO MDS registry <https://fidoalliance.org/metadata/>`_ of
   FIDO-certified authenticators, complimented with community contributions.

Installation
------------

Install ``django_otp_webauthn`` with the ``identify`` extra:

.. code-block:: console

    pip install django_otp_webauthn[identify]

This will install the required `python-identify-passkey
<https://github.com/Stormbase/python-identify-passkey>`_ library which
contains the most up-to-date list of Passkey identifiers.

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

If you don't have a :setting:`STATICFILES_FINDERS` setting yet,
you can add it like this:

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
Passkeys in your application. For example, you could use the inferred name of
the authenticator as fallback name for a Passkey in your user interface, or show
the icon of the authenticator next to the Passkey name.

``AbstractWebAuthnCredential.identify``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can use the :meth:`django_otp_webauthn.models.AbstractWebAuthnCredential.identify` method to directly identify a credential instance.

When identifiable, this will give you a :class:`django_otp_webauthn.contrib.identify.PasskeyDescriptor` object, which contains the name of the authenticator and – in almost all cases – a light and dark icon.

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

Credentials now also have an :attr:`django_otp_webauthn.models.AbstractWebAuthnCredential.inferred_name` property, which will return the name of the authenticator if it can be identified, or ``None`` if it cannot.

.. code-block:: python

    from django_otp_webauthn.models import WebAuthnCredential

    credential = WebAuthnCredential.objects.get(pk=1)
    print(credential.inferred_name)  # Apple Passwords


Accessing without a credential instance
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Alternatively, you can use the :func:`django_otp_webauthn.contrib.identify.identify_passkey` function to identify a Passkey directly by its AAGUID.

.. code-block:: python

    from django_otp_webauthn.contrib.identify import identify_passkey

    aaguid = "fbfc3007-154e-4ecc-8c0b-6e020557d7bd"  # Apple Passwords AAGUID
    passkey_descriptor = identify_passkey(aaguid)

    if passkey_descriptor:
        print(repr(passkey_descriptor))  # PasskeyDescriptor(name='Apple Passwords', aaguid='fbfc3007-154e-4ecc-8c0b-6e020557d7bd')
        print(repr(passkey_descriptor.icon_light)) # PasskeyIcon(theme='light', mime='image/svg+xml', path='/path/to/svg/file.svg')
        print(repr(passkey_descriptor.icon_dark)) # PasskeyIcon(theme='dark', mime='image/svg+xml', path='/path/to/svg/file.svg')
