.. _about-passkeys:

About passkeys
==============

:term:`Passkeys <passkey/discoverable credential>` are a more secure alternative to passwords. Passwords require users to remember and type in secret combinations of words, numbers, or characters. In contrast, passkeys are securely stored on a user's device and accessed through the device's biometric sensor, PIN, or pattern.

A major risk associated with using passwords is that they are a **shared secret**, meaning the server also stores your password. If the server stores it insecurely and it gets leaked, your security is compromised. Passkeys remove this risk by ensuring that the server stores only the :term:`public key`. The stored public key is worthless without the corresponding :term:`private key` stored securely on your device.

Also, many people reuse passwords across different accounts, making them vulnerable to an attack known as **credential stuffing**. In these attacks, malicious actors try known username-password combinations from one site to other sites to gain unauthorized access. Passkeys remove this risk, as each passkey :term:`key pair` is unique and can't be reused across services.

Passkeys also make the login process more convenient and seamless. Users simply confirm their identity by answering **yes** on a login prompt, using either their device's biometric sensor or a PIN.

How passkeys work
-----------------

To register a passkey, you first sign in to an online service using an existing authentication method. Once you approve the creation of a passkey, your device’s password manager generates a unique cryptographic key pair. It securely stores the private key, while the public key is registered with the online service.

When you sign in with a passkey, the server sends a random challenge to your device. Depending on the server's settings, your device may prompt you to verify your identity using biometrics, a PIN, or another security method, or it may simply ask for your confirmation. Once you respond, your device signs the challenge with your private key and sends it back to the server. The server authenticates the signed challenge against the stored public key and grants you access.
