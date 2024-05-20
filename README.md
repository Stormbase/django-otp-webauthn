# Django OTP WebAuthn

This package provides an implementation of [WebAuthn Passkeys](https://passkeys.dev/) for Django. It is written as a plugin for the [Django OTP framework](https://github.com/django-otp/django-otp) for multi-factor authentication. Under the hood, this package uses [py_webauth](https://github.com/duo-labs/py_webauthn/) to handle all cryptographic operations.

> [!IMPORTANT]  
> This package is still in development and is not yet ready for production use. The API is subject to change. If you are interested in using this package, please star this repository to show your interest. This will help me prioritize development. If you are interested in contributing, please see the [DEVELOPMENT.md](DEVELOPMENT.md) file.

- [Django OTP WebAuthn](#django-otp-webauthn)
  - [Compatibility](#compatibility)
    - [Browser compatibility](#browser-compatibility)
  - [Features](#features)
  - [Quick start guide - how to use Passkeys in your Django project](#quick-start-guide---how-to-use-passkeys-in-your-django-project)
  - [What exactly is a Passkey?](#what-exactly-is-a-passkey)
    - [How Passkeys work (in a nutshell)](#how-passkeys-work-in-a-nutshell)
    - [Why use Passkeys?](#why-use-passkeys)
    - [A note about security](#a-note-about-security)
  - [Who uses Passkeys?](#who-uses-passkeys)
  - [Further reading](#further-reading)
  - [Development](#development)
  - [License](#license)

## Compatibility

- Django >= 4.2
- Python >= 3.9
- django-otp >= 1.2.0

### Browser compatibility

Passkeys are supported in most modern browsers. Here is a list of browsers that support Passkeys:

- Chrome 67+
- Firefox 60+
- Safari 13+
- Microsoft Edge 18+

For a complete list, see [caniuse.com/webauthn](https://caniuse.com/webauthn).

## Features

- **Passkeys as a second factor.** Lets users just click yes on the browser prompt to verify their identity after they have entered their password.
- **Passwordless login with Passkeys (optional).** Lets users verify their identity using a biometric sensor, security key, or other compatible device. Can be disabled if you prefer to use Passkeys as a second factor only.
- **Batteries included.** comes with a default frontend JavaScript implementation that works out of the box and removes complexity for you.
- **Flexible frontend.** you can style the fronted implementation to fit your brand. Or roll your own frontend implementation if you need something more custom.
- **Compatible with strict [Content Security Policy (CSP)](https://content-security-policy.com/).** The frontend implementation does not rely on inline scripts and is compatible with strict CSP settings.

## Quick start guide - how to use Passkeys in your Django project

To quickly start using Passkeys in your Django project, follow these steps:

1. Install the package from PyPI:

   ```bash
   pip install django-otp-webauthn
   ```

2. Add `django_otp_webauthn` to your `INSTALLED_APPS` in your Django settings:

   ```python
   INSTALLED_APPS = [
       ...
       "django_otp_webauthn",
       ...
   ]
   ```

3. Add the required URLs to your Django project:

   ```python
   # urls.py

   from django.urls import include, path

   urlpatterns = [
       ...
       path("webauthn/", include("django_otp_webauthn.urls", namespace="otp_webauthn")),
       ...
   ]
   ```

4. Add required settings to your Django settings. This example assumes you want to configure for `localhost`. You will need to adjust the settings for your production environment.

   ```python
   # settings.py

   # The name of the relying party (RP). This is sometimes shown to the user when they register a Passkey.
   OTP_WEBAUTHN_RP_NAME = "My Website Inc."
   # This is necessary to bind the Passkey to a specific domain. This should be the domain of your website.
   OTP_WEBAUTHN_RP_ID = "localhost"
   # This is used to check the origin of the request and is used for security. It is similar to Django's CSRF_TRUSTED_ORIGINS setting.
   # The origins must always be a subdomain of the RP ID or the RP ID itself.
   OTP_WEBAUTHN_ALLOWED_ORIGINS = ["http://localhost"]

   ```

5. Add the registration code to your logged-in user template.

   ```html
   <!-- logged_in_template.html -->
   {% load otp_webauthn %}

   {% comment %}
   This template is displayed when WebAuthn registration is supported.
   The template must contain a button with the id `passkey-register-button`. To display status and error messages, include an element with the id `passkey-register-status-message`.
   {% endcomment %}
   <template id="passkey-registration-available-template">
       <div>
           <button type="button" id="passkey-register-button">Register Passkey</button>
           <div id="passkey-register-status-message"></div>
       </div>
   </template>

   {% comment %}
   This template is displayed when WebAuthn registration is not supported.
   {% endcomment %}
   <template id="passkey-registration-unavailable-template">
       <p>Sorry, your browser has no Passkey support</p>
   </template>

   {% comment %}
   This placeholder element will be replaced with either the contents of the `passkey-registration-available-template` or the `passkey-registration-unavailable-template` template.
   {% endcomment %}
   <span id="passkey-registration-placeholder"></span>

   {% comment %}
   This template tag renders all the necessary <script> tags for the default registration implementation
   {% endcomment %}
   {% render_otp_webauthn_register_scripts %}
   ```

6. On your login page, include the following to enable passwordless login:

   ```html
   {% load otp_webauthn %}

   <form method="post">
       {# Suppose there is an username field on your page that has CSS selector: input[name="username"] #}
       <label for="id_username">Username</label>
       <input id="id_username" type="text" name="username" autocomplete="username">
       {# Other fields omitted for brevity #}

       {# This placeholder element will be replaced with either the contents of the `passkey-verification-available-template` or the `passkey-verification-unavailable-template` template. #}
       <span id="passkey-verification-placeholder"></span>

       {% comment %}
       This template is displayed when WebAuthn authentication is supported. Typically, you would want to display a button that the user can click to authenticate using a Passkey.
       The template must contain a button with the id `passkey-verification-button`. To display status and error messages, include an element with the id `passkey-verification-status-message`.
       {% endcomment %}
       <template id="passkey-verification-available-template">
           <button type="button" id="passkey-verification-button">Login using a Passkey</button>
           <div id="passkey-verification-status-message"></div>
       </template>


       {% comment %}
       This template is displayed when WebAuthn is not supported.
       {% endcomment %}
       <template id="passkey-verification-unavailable-template">
           <p>Sorry, your browser has no Passkey support</p>
       </template>

       {% comment %}
       This template tag renders all the necessary <script> tags for the default verification implementation

       To make browsers automatically suggest a Passkey when you focus the username
       field, make sure `username_field_selector` is a valid CSS selector.
       {% endcomment %}
       {% render_otp_webauthn_auth_scripts username_field_selector="input[name='username'] %}
   </form>
   ```

7. Don't forget to run migrations:

   ```sh
   python manage.py migrate
   ```

8. That's it! You should now see a "Register Passkey" button on your logged-in user template. Clicking this button will start the registration process. After registration, you should see a "Login using a Passkey" button on your login page. Clicking this button will prompt you to use your Passkey to authenticate. Or if your browser supports it, you will be prompted to use your Passkey when you focus the username field.

## What exactly is a Passkey?

Passkeys are a new way to authenticate on the web. Officially they are called 'WebAuthn credentials', but Passkeys are the more memorable, human-friendly name, that has been chosen to describe them. They allow users of your site to use their phone, laptop, security key, or other compatible device to authenticate without having to remember a password.

Passkeys follow the [WebAuthn](https://www.w3.org/TR/webauthn-3/) standard. The standard describes a way to use [public-key cryptography](https://en.wikipedia.org/wiki/Public-key_cryptography) to authenticate users.

### How Passkeys work (in a nutshell)

Here is an (overly simplified) explanation of how Passkeys work. For a more detailed explanation, try [Auth0's interactive WebAuthn demo](https://webauthn.me/). It has a very nice explanation of the WebAuthn flow! Or dive into the [WebAuthn standard](https://www.w3.org/TR/webauthn-3/) itself.

1. An already authenticated user registers a Passkey with your site. A public-private key pair is generated on the user's device. The private key is stored securely and the public key is sent to the server and associated with the authenticated user. An additional piece of information is also stored on the server, called the 'credential ID'.
2. When a user wants to authenticate, the server sends a challenge to the user's device. The user's device signs the challenge with the private key and sends the signature back to the server along with the credential ID.
3. The server looks up the public key associated with the given credential ID and uses it to check the signature. Was this signature generated by the private key that belongs to the public key we have on file? If yes, the user must be in possession of the private key and is authenticated.

### Why use Passkeys?

- **Security.** Compared to passwords, Passkeys are resistant to phishing attacks, credential stuffing, and other common attacks.
- **Convenience.** Passkeys are more convenient than passwords. Users don't have to choose and remember a password, they can use their phone, laptop, or security key to authenticate. Compared to other traditional forms of Multi Factor Authentication, there is no need to wait for an SMS code to arrive or copy a code from an authenticator app. Just click yes on the browser prompt.

### A note about security

Passkeys are sometimes claimed to be silver bullet for security. While they are more secure than passwords, they are not perfect.

You put trust in the user's device and its manufacturer. Most devices support some form is syncing Passkeys between devices, like through an iCloud or Google account. This means that if someone gains access to the users' iCloud or Google account, they could potentially access their Passkeys. Users that have poorly secured their account and devices are at risk. However, this is not unique to Passkeys. The same risks exists for password managers and other forms of Multi Factor Authentication that support syncing between devices. Passkeys improve over other methods by their resistance to phishing attacks, credential stuffing and their convenience.

It is the author's opinion that the benefits of Passkeys outweigh the risks. This section is here for your own consideration.

## Who uses Passkeys?

Plenty of websites already support Passkeys. Here are some well known examples:

- [GitHub](https://docs.github.com/en/authentication/authenticating-with-a-passkey/signing-in-with-a-passkey)
- [Google](https://support.google.com/accounts/answer/13548313?hl=en)
- [Microsoft](https://support.microsoft.com/en-us/account-billing/set-up-a-security-key-as-your-verification-method-2911cacd-efa5-4593-ae22-e09ae14c6698)
- [Whatsapp](https://www.threads.net/@wcathcart/post/Cyd27d7pex8)

It is about time for your website to support Passkeys too!

## Further reading

Here are some good resources to learn more about Passkeys:

- [Passkeys.dev](https://passkeys.dev/) - general information about Passkeys
- [Auth0's WebAuthn demo](https://webauthn.me/) - has a very nice explanation of the WebAuthn flow!
- [The WebAuthn standard (working draft)](https://www.w3.org/TR/webauthn-3/)

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for information on how to develop and contribute to this project.

## License

This project is licensed under the BSD 3-Clause License. See the [LICENSE](LICENSE) file for details.
