.. django-otp-webauthn-doc documentation master file, created by
   sphinx-quickstart on Thu Sep 26 15:47:57 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Django OTP WebAuthn
===================

|Version| |License| |Build Status| |codecov| |All Contributors| |pre-commit|

This package provides an implementation of `WebAuthn Passkeys <https://passkeys.dev/>`_ for Django. It is written as a plugin for the `Django OTP framework <https://github.com/django-otp/django-otp>`_ for multi-factor authentication. Under the hood, this package uses `py_webauth <https://github.com/duo-labs/py_webauthn/>`_ to handle all cryptographic operations.

.. important::
   This package is in development not yet thoroughly tested and documented. The API is subject to change. If you are interested in using this package, please star this repository to show your interest. This will help me prioritize development. If you are interested in contributing, please see the `DEVELOPMENT.md <DEVELOPMENT.md>`_ file.

Compatibility
-------------

- Django >= 4.2
- Python >= 3.9
- django-otp >= 1.4.0

Browser Compatibility
^^^^^^^^^^^^^^^^^^^^^

Passkeys are supported in most modern browsers. Here is a list of browsers that support Passkeys:

- Chrome 67+
- Firefox 60+
- Safari 13+
- Microsoft Edge 18+

For a complete list, see `caniuse.com/webauthn <https://caniuse.com/webauthn>`_.

Features
--------

- **Passkeys as a second factor.** Lets users just click yes on the browser prompt to verify their identity after they have entered their password.
- **Passwordless login with Passkeys (optional).** Lets users verify their identity using a biometric sensor, security key, or other compatible device. Can be disabled if you prefer to use Passkeys as a second factor only.
- **Batteries included.** comes with a default frontend JavaScript implementation that works out of the box and removes complexity for you.
- **Flexible frontend.** you can style the fronted implementation to fit your brand. Or roll your own frontend implementation if you need something more custom.
- **Compatible with strict** `Content Security Policy (CSP) <https://content-security-policy.com/>`_. The frontend implementation does not rely on inline scripts and is compatible with strict CSP settings.

Quick Start Guide
-----------------

To quickly start using Passkeys in your Django project, follow these steps:

1. Install the package from PyPI:

   .. code-block:: bash

      pip install django-otp-webauthn

2. Add ``django_otp_webauthn`` to your ``INSTALLED_APPS`` in your Django settings:

   .. code-block:: python

      INSTALLED_APPS = [
          ...
          "django_otp_webauthn",
          ...
      ]

3. Add the required URLs to your Django project:

   .. code-block:: python

      # urls.py
      from django.urls import include, path

      urlpatterns = [
          ...
          path("webauthn/", include("django_otp_webauthn.urls", namespace="otp_webauthn")),
          ...
      ]

4. Add required settings to your Django settings:

   .. code-block:: python

      # settings.py

      # The name of the relying party (RP)
      OTP_WEBAUTHN_RP_NAME = "My Website Inc."
      # Domain binding for Passkey
      OTP_WEBAUTHN_RP_ID = "your-domain.com"
      # Allowed origins
      OTP_WEBAUTHN_ALLOWED_ORIGINS = [
          "https://your-domain.com",
          "https://subdomain.your-domain.com"
      ]

5. Add WebAuthn Backend (optional):

   .. code-block:: python

      AUTHENTICATION_BACKENDS = [
          ...
          "django_otp_webauthn.backends.WebAuthnBackend",
          ...
      ]

6. Add registration code to your logged-in user template:

   .. code-block:: html

      {% load otp_webauthn %}

      <template id="passkey-registration-available-template">
          <div>
              <button type="button" id="passkey-register-button">Register Passkey</button>
              <div id="passkey-register-status-message"></div>
          </div>
      </template>

      <template id="passkey-registration-unavailable-template">
          <p>Sorry, your browser has no Passkey support</p>
      </template>

      <span id="passkey-registration-placeholder"></span>

      {% render_otp_webauthn_register_scripts %}

7. On your login page, include the following:

   .. code-block:: html

      {% load otp_webauthn %}

      <form method="post">
          <input id="id_username" type="text" name="username" autocomplete="username">

          <span id="passkey-verification-placeholder"></span>

          <template id="passkey-verification-available-template">
              <button type="button" id="passkey-verification-button">Login using a Passkey</button>
              <div id="passkey-verification-status-message"></div>
          </template>

          <template id="passkey-verification-unavailable-template">
              <p>Sorry, your browser has no Passkey support</p>
          </template>

          {% render_otp_webauthn_auth_scripts username_field_selector="input[name='username']" %}
      </form>

8. Run migrations:

   .. code-block:: bash

      python manage.py migrate

Using Custom Credential and Attestation Models
----------------------------------------------

.. code-block:: python

   from django.db import models
   from django_otp_webauthn.models import AbstractWebAuthnAttestation, AbstractWebAuthnCredential

   class MyCredential(AbstractWebAuthnCredential):
       pass

   class MyAttestation(AbstractWebAuthnAttestation):
       credential = models.OneToOneField(
           MyCredential,
           on_delete=models.CASCADE,
           related_name="attestation",
           editable=False
       )

What is a Passkey?
------------------

Passkeys are a new way to authenticate on the web. Officially they are called 'WebAuthn credentials', but Passkeys are the more memorable, human-friendly name. They allow users to authenticate without remembering passwords.

How Passkeys Work
^^^^^^^^^^^^^^^^^

1. An authenticated user registers a Passkey, generating a public-private key pair.
2. When authenticating, the user's device signs a challenge with the private key.
3. The server verifies the signature using the stored public key.

Why Use Passkeys?
^^^^^^^^^^^^^^^^^

- **Security:** Resistant to phishing attacks and credential stuffing.
- **Convenience:** No need to remember passwords or wait for SMS codes.

Security Considerations
^^^^^^^^^^^^^^^^^^^^^^^

While more secure than passwords, Passkeys are not perfect. They rely on the security of the user's device and account syncing mechanisms.

Who Uses Passkeys?
------------------

- GitHub
- Google
- Microsoft
- Whatsapp

Further Reading
---------------

- `Passkeys.dev <https://passkeys.dev/>`_
- `Auth0's WebAuthn demo <https://webauthn.me/>`_
- `WebAuthn Standard <https://www.w3.org/TR/webauthn-3/>`_

Development
-----------

See `DEVELOPMENT.md <DEVELOPMENT.md>`_ for development and contribution information.

License
-------

This project is licensed under the BSD 3-Clause License. See the `LICENSE <LICENSE>`_ file for details.

.. |Version| image:: https://img.shields.io/pypi/v/django-otp-webauthn.svg
   :target: https://pypi.python.org/pypi/django-otp-webauthn/

.. |License| image:: https://img.shields.io/badge/license-BSD-blue.svg
   :target: https://opensource.org/licenses/BSD-3-Clause

.. |Build Status| image:: https://github.com/Stormbase/django-otp-webauthn/actions/workflows/test.yml/badge.svg
   :target: https://github.com/Stormbase/django-otp-webauthn/actions/workflows/test.yml

.. |codecov| image:: https://codecov.io/gh/Stormheg/django-otp-webauthn/graph/badge.svg
   :target: https://codecov.io/gh/Stormheg/django-otp-webauthn

.. |All Contributors| image:: https://img.shields.io/github/all-contributors/Stormbase/django-otp-webauthn?color=ee8449
   :target: #contributors

.. |pre-commit| image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit
   :target: https://github.com/pre-commit/pre-commit


.. toctree::
   :maxdepth: 2
   :hidden:

   test-content/development
