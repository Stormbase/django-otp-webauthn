About Django OTP WebAuthn
=========================

Django OTP WebAuthn is an implementation of `WebAuthn Passkeys <https://passkeys.dev>`_ for Django applications. It extends the `django-otp <https://github.com/django-otp/django-otp>`_ framework to support multi-factor authentication using :ref:`passkeys <about-passkeys>`.

Django OTP WebAuthn simplifies :term:`passkey` authentication by handling all cryptographic operations through `py_webauthn <https://github.com/duo-labs/py_webauthn/>`_.

Features
--------

Django OTP WebAuthn comes with the following built-in features:

* **Passkeys as a second-factor authentication:** Users can verify their identity by approving a browser prompt after entering their password.

* **Passwordless login:** Users can authenticate without a password using biometrics, a security key, or another trusted device. You can disable this feature if you want to use Django OTP WebAuthn as :term:`second-factor authentication`.

* **Batteries:** Comes with a default frontend JavaScript implementation that works out of the box.

* **Flexible frontend:** Users can customize the default UI to match their brand or implement a fully custom frontend.

* **Strict Content Security Policy (CSP) compatibility:** The frontend implementation doesn't rely on inline scripts and is compatible with strict CSP settings.

.. _compatibility:

Compatibility
-------------

Django OTP WebAuthn is compatible with the following versions:

* Django >= 4.2

* Python >= 3.9

* django-otp >= 1.4.0

Browser support
---------------

Django OTP WebAuthn works with most modern browsers that support WebAuthn passkeys, including:

* Google Chrome 67+

* Mozilla Firefox 60+

* Apple Safari 13+

* Microsoft Edge 18+

For a complete list of supported browsers, see `Web Authentication API support on caniuse.com <https://caniuse.com/webauthn>`_.


.. toctree::
   :maxdepth: 2
   :hidden:

   Getting started <getting_started/index.rst>
   Customizing behavior <customizing_behavior/index.rst>
   Reference <reference/index.rst>
   limitations.rst
   glossary.rst
   Contributing <contributing/index.rst>
