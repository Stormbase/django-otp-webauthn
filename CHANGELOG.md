# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.3] - [UNRELEASED]

### Added

- The default manager for the `WebAuthnCredential` model now includes a `as_credential_descriptors` method to make it easier to format the credentials for use in custom implementations.

### Fixed

- A bug was fixed with Python 3.11 and older that caused an exception when authenticating with a WebAuthn credential. ([#6](https://github.com/Stormbase/django-otp-webauthn/pull/6) by [jmichalicek](https://github.com/jmichalicek))

### Changed

- The `http://localhost:8000` default value for `OTP_WEBAUTHN_ALLOWED_ORIGINS` was removed.
- Use more appropriate examples for the `OTP_WEBAUTHN_*` settings in the README.
- Update admonition in the README to reflect the current state of the project. We have moved from don't use in production to use at your own risk.

## [0.1.2] - 2024-06-12

### Fixed

- The helper classes' `get_credential_display_name` and `get_credential_name` methods are now correctly called. Previously, the users' full name was being used as the credential name, bypassing above methods.

### Changed

- Set discoverable credential policy to `required` at registration time when `OTP_WEBAUTHN_ALLOW_PASSWORDLESS_LOGIN` is set to `True`. This is to ensure a credential capable of passwordless login is created.

### New

- Make is easier to override the helper class using the new `OTP_WEBAUTHN_HELPER_CLASS` setting. Pass it a dotted path to your custom helper class and it will be used instead of the default one.

## [0.1.1] - 2024-05-26

### Fixed

- An issue with the button label not showing any text was fixed.

### Changed

- `WebAuthnCredential` now inherits from `django_otp.models.TimestampMixin` to add a `created_at` and `last_used_at` fields. Subsequently, this raises the minimum `django-otp` version to `1.4.0+`.

### Maintenance

- Switch to [`hatch`](https://hatch.pypa.io/) for managing the project.

## [0.1.0] - 2024-05-12

- Initial release.
