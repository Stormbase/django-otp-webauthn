# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2024-05-26

### Fixed

- An issue with the button label not showing any text was fixed.

### Changed

- `WebAuthnCredential` now inherits from `django_otp.models.TimestampMixin` to add a `created_at` and `last_used_at` fields. Subsequently, this raises the minimum `django-otp` version to `1.4.0+`.

### Maintenance

- Switch to [`hatch`](https://hatch.pypa.io/) for managing the project.

## [0.1.0] - 2024-05-12

- Initial release.
