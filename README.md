# Passkeys for Django OTP

This repository (soon-to-be-a-proper-python-package) is my proof of concept for adding support for [Passkeys](https://passkeys.dev/) to Django. This package extends the [Django OTP](https://github.com/django-otp/django-otp) library and uses the [python-fido2](https://github.com/Yubico/python-fido2/) to handle all cryptographic operations.

## What is a Passkey?

A Passkey is a passwordless authentication method that uses the [WebAuthn](https://www.w3.org/TR/webauthn-3/) standard. It allows users to use their phone, laptop, security key or other compatible device to authenticate without having to remember a password.

- 🔒 It is more private than a password because it uses public key cryptography and the server never sees your private key. The server only sees a public key and uses that to verify that you are in possession of the private key.
- 🤖 It is more convenient than a password because you don't have to remember it. You can use your phone, laptop or security key to authenticate. You can even have multiple Passkeys registered at the same time.
- 🎉 [No need to create a password with capital letters, numbers and special characters](https://neal.fun/password-game/). You can use a simple PIN or biometric authentication (e.g. fingerprint or face recognition) to unlock your Passkey.
- ☁️ Passkeys created using Safari or Chrome travel with you because they are stored **securely** in the cloud.
- 📱 Need to login on a new device? No problem! Some Passkeys, like the ones stored on your Android or iPhone, can be used to verify your identity on a new device via a Bluetooth connection. These are called a roaming authenticators in WebAuthn terms. It is also possible to use a security key to verify your identity on a new device.

## Who uses Passkeys?

Plenty of websites already support Passkeys. Here are some well known examples:

- [GitHub](https://docs.github.com/en/authentication/authenticating-with-a-passkey/signing-in-with-a-passkey)
- [Google](https://support.google.com/accounts/answer/13548313?hl=en)
- [Microsoft](https://support.microsoft.com/en-us/account-billing/set-up-a-security-key-as-your-verification-method-2911cacd-efa5-4593-ae22-e09ae14c6698)
- [Whatsapp](https://www.threads.net/@wcathcart/post/Cyd27d7pex8)

It is about time for your website to support Passkeys too!

## Links

- [Passkeys.dev](https://passkeys.dev/) - general information about Passkeys
- [Auth0's WebAuthn demo](https://webauthn.me/) - has a very nice explanation of the WebAuthn flow!
- [The WebAuthn standard (working draft)](https://www.w3.org/TR/webauthn-3/)

## Requirements

- Python 3.8+
- Node 20+
- Yarn
- [Caddy](https://github.com/caddyserver/caddy) - WebAuthn requires HTTPS on a proper domain (non-localhost or .test domain), so you need to use a reverse proxy like Caddy that supports automatic HTTPS. You could also use [ngrok](https://ngrok.com/) for testing purposes, but I haven't tried that yet.

## Installation (sandbox)

Create a new virtual environment

    python -m venv venv

    # Linux / Mac
    source venv/bin/activate

    # Windows
    venv\Scripts\activate.bat

Install the requirements

    python -m pip install -r requirements.txt

Create a superuser

    python manage.py createsuperuser

Install and build the frontend dependencies

    cd client
    yarn install
    yarn watch

If using Caddy, you need to add the `passkey-demo.xyz` domain to your hosts file (because it is not a real domain)

    # Linux / Mac
    sudo echo "127.0.0.1 passkey-demo.xyz" >> /etc/hosts

    # Windows (run as administrator)
    echo "127.0.0.1 passkey-demo.xyz" >> %WINDIR%\System32\drivers\etc\hosts

If this is the first time you are running Caddy, you need to install the Caddy certificate authority (CA) certificate. This is needed to trust the self-signed certificates that Caddy generates for your local domains.

    caddy trust

## Usage (sandbox)

Run the development server

    python manage.py runserver

And run Caddy (reverse proxy with https) in a separate terminal

    caddy run

You can now access the sandbox at [https://passkey-demo.xyz/](https://passkey-demo.xyz/)

From here you can login using the superuser you created. You can register a passkey by clicking the "_Register passkey_" button. The "_verify now_" link will take you to the verification page where you can use your passkey to verify.

Additionally – once you've registered a passkey – your browser should prompt you to use your passkey when logging in. Completely passwordless!

## What is working?

- [x] Registering a passkey
- [x] Logging in using a passkey (passwordless login)
- [x] Using your passkey as a second factor (2FA)
- [x] Compatible with strict [Content Security Policy (CSP)](https://content-security-policy.com/)

## Known issues

- I'm having issues using my Android 14 Pixel 5 as a roaming authenticator for passwordless logins (strangely it works properly when using already logged in and assing the 'verify now' link). It's telling me there are no passkeys available. I can do passwordless logins on GitHub using my Pixel so I'm guessing it's a bug in my code. I'm still investigating this.

## Where is this going?

I'm not entirely sure yet. I'm still trying to figure out what features to support and what a mature version should look like. Like django-otp, this will likely be a low-level library that makes little to no assumptions about your frontend (except that you are using Django's template system maybe).

I work on this in my free time so it might take a while before I have something that I dare put in production. Sponsorship would help speed up the development process, contact me if you are interested (email: [my first name] [at] stormbase.digital)

## Incomplete and non-exhaustive list of things I want to do

- [ ] Test this with a real Django project and see what is missing or could be improved. Could perhaps function as a reference implementation too.
- [ ] Integrate with [wagtail-2fa](https://github.com/labd/wagtail-2fa) because I use Wagtail a lot
- [ ] Refactor ugly code (especially the frontend has become quite the spaghetti 🍝, Mama Mia!)
- [ ] Figure out how to properly handle errors from python-fido2, maybe contribute some fixes upstream?
- [ ] Allow the frontend to be more customizable. Likely by raising events that can be listened to (e.g. `otp_passkey:registration-start`, `passkey:registration-complete`, etc.) The developer can then use these events to update the UI.
  - [x] Some of this is already implemented using `<template>` elements that can be customized by the developer. This needs to be expanded too.
- [ ] Add unit tests
- [ ] Add end-to-end tests (playwright?) - there is quite some interaction between browser apis, frontend and backend so this would be very useful I think
- [ ] Write documentation for developers using this library in their own projects

## Out of scope

- Verifying passkey attestation statements. I consider this is too complex and implementation specific to be included in this library.
- Support for WebAuthn extensions. I don't think this is needed for most use cases. Might add some helpers for this later, but I don't think I will add support for this in the core library.

## License

This project is licensed under the BSD 3-Clause License. See the [LICENSE](LICENSE) file for details.
