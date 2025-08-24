import base64
import hashlib
from datetime import timedelta

import pytest
from django.db import IntegrityError
from django.test.utils import isolate_apps
from django.utils import timezone
from webauthn.helpers.structs import (
    AttestationObject,
    AuthenticatorTransport,
    PublicKeyCredentialDescriptor,
)

from django_otp_webauthn.checks import ERR_ATTESTATION_MISSING_CREDENTIAL_FIELD
from django_otp_webauthn.helpers import WebAuthnHelper
from django_otp_webauthn.models import (
    AbstractWebAuthnAttestation,
    WebAuthnAttestation,
    WebAuthnAttestationManager,
    WebAuthnCredential,
    WebAuthnCredentialManager,
    WebAuthnUserHandle,
    as_credential_descriptors,
)
from tests.factories import (
    UserFactory,
    WebAuthnAttestationFactory,
    WebAuthnCredentialFactory,
)


def test_imports():
    """The following imports should work."""


@pytest.mark.django_db
def test_as_credential_descriptors(user):
    """Test that the as_credential_descriptors function works."""
    credential_1 = WebAuthnCredentialFactory(
        user=user, transports=["hybrid", "ble", "made_up_transport"]
    )

    descriptors = as_credential_descriptors(WebAuthnCredential.objects.all())
    assert len(descriptors) == 1

    descriptor = descriptors[0]
    assert isinstance(descriptor, PublicKeyCredentialDescriptor)
    assert descriptors[0].id == credential_1.credential_id
    # Order is important, should be the same as the order in the transports field. Made up transport is not a known transport and will be ignored.
    assert descriptors[0].transports == [
        AuthenticatorTransport.HYBRID,
        AuthenticatorTransport.BLE,
    ]


@pytest.mark.django_db
def test_attestation_str():
    """Test that the __str__ method of the attestation model works."""
    attestation = WebAuthnAttestationFactory(fmt="packed")

    credential_str = str(attestation.credential)

    assert str(attestation) == f"{credential_str} (fmt=packed)"


@pytest.mark.django_db
def test_attestation_parse_attestation_object():
    """Test that the parse_attestation_object method works."""

    attestation = WebAuthnAttestationFactory(
        # Sample attestation object with fmt=none
        data=base64.b64decode(
            "o2NmbXRkbm9uZWdhdHRTdG10oGhhdXRoRGF0YVikSZYN5YgOjGh0NBcPZHZgW4/krrmihjLHmVzzuoMdl2NFAAAAAQAAAAAAAAAAAAAAAAAAAAAAIOluordQzlAm3qHGmv9E6c9rYD013JHCS+gMLN4Oou0DpQECAyYgASFYIIkvmz/Bg+B4lrMV5QzilURGaWu5GR0XhpgZmo+muwjcIlgg3mH0Z52MFDWupNlxOxYGCA3HibDWKTMZJT+vI2MUc+w="
        )
    )

    att_obj = attestation.attestation_object

    assert isinstance(attestation.attestation_object, AttestationObject)
    assert att_obj.fmt == "none"


@pytest.mark.django_db
def test_attestation_manager():
    assert isinstance(WebAuthnAttestation.objects, WebAuthnAttestationManager)


def test_attestation_custom_model_missing_credential_field():
    """Test that the custom model check fails when the credential field is missing."""
    with isolate_apps("django_otp_webauthn"):

        class MyAttestation(AbstractWebAuthnAttestation):
            # Missing the credential field
            class Meta:
                app_label = "django_otp_webauthn"

        errors = MyAttestation.check()
        assert len(errors) == 1
        assert errors[0].id == ERR_ATTESTATION_MISSING_CREDENTIAL_FIELD


@pytest.mark.django_db
def test_credential_hash_created_on_save():
    """Test that the credential_id_sha256 is created on save."""
    credential_id = b"credential_id"
    expected_hash_sha256 = hashlib.sha256(credential_id).hexdigest()

    credential = WebAuthnCredentialFactory(credential_id=credential_id)
    credential.save()
    assert credential.credential_id_sha256 == expected_hash_sha256


@pytest.mark.django_db
def test_credentials_are_unique():
    """Test that it is impossible to create credentials sharing the same credential id."""
    credential_id = b"credential_id"

    cred1 = WebAuthnCredentialFactory(credential_id=credential_id)

    with pytest.raises(IntegrityError):
        cred2 = WebAuthnCredentialFactory()
        assert cred2.pk is not cred1.pk
        cred2.credential_id = credential_id
        cred2.credential_id_sha256 = None

        # At this point, the hash will be generated and the unique constraint will be violated.
        cred2.save()


@pytest.mark.django_db
def test_get_by_credential_id(django_assert_num_queries):
    """Test that the get_by_credential_id method works."""
    credential_id = b"credential_id"

    cred1 = WebAuthnCredentialFactory(credential_id=credential_id)

    with django_assert_num_queries(1):
        assert WebAuthnCredential.get_by_credential_id(credential_id) == cred1

    with pytest.raises(WebAuthnCredential.DoesNotExist):
        assert (
            WebAuthnCredential.get_by_credential_id(b"non_existent_credential_id")
            is None
        )


def test_get_credential_id_sha256():
    """Test that the get_credential_id_sha256 method works."""
    credential_id = b"credential_id"
    expected_hash_sha256 = hashlib.sha256(credential_id).hexdigest()

    assert (
        WebAuthnCredential.get_credential_id_sha256(credential_id)
        == expected_hash_sha256
    )


@pytest.mark.django_db
def test_credential_get_credential_descriptors_for_user(user):
    """Test that the get_credential_descriptors_for_user method works."""
    other_user = UserFactory()

    credential_1 = WebAuthnCredentialFactory(
        user=user, transports=["hybrid", "ble"], last_used_at=None
    )
    credential_2 = WebAuthnCredentialFactory(
        user=user,
        transports=["internal", "made_up_transport"],
        last_used_at=timezone.now() - timedelta(days=1),
    )
    credential_3 = WebAuthnCredentialFactory(
        user=user, transports=["nfc"], last_used_at=timezone.now()
    )

    WebAuthnCredentialFactory(user=other_user, transports=["usb"])

    descriptors = WebAuthnCredential.get_credential_descriptors_for_user(user)
    assert len(descriptors) == 3

    # When using the classmethod, the credentials will be ordered by last_used_at, with the most recently used first.
    # See source code comment for explanation as to why this is done.
    assert descriptors[0].id == credential_3.credential_id
    assert descriptors[0].transports == [AuthenticatorTransport.NFC]
    assert descriptors[1].id == credential_2.credential_id
    assert descriptors[1].transports == [AuthenticatorTransport.INTERNAL]
    assert descriptors[2].id == credential_1.credential_id
    assert descriptors[2].transports == [
        AuthenticatorTransport.HYBRID,
        AuthenticatorTransport.BLE,
    ]


def test_credential_manager():
    """Default manager should be the custom manager."""
    assert isinstance(WebAuthnCredential.objects, WebAuthnCredentialManager)


@pytest.mark.django_db
def test_credential_queryset_as_credential_descriptors():
    """Test that the as_credential_descriptors method works on a queryset."""
    credential_1 = WebAuthnCredentialFactory(transports=["hybrid", "ble"])
    credential_2 = WebAuthnCredentialFactory(
        transports=["internal", "made_up_transport"]
    )

    descriptors = (
        WebAuthnCredential.objects.all().order_by("id").as_credential_descriptors()
    )
    assert len(descriptors) == 2
    assert descriptors[0].id == credential_1.credential_id
    assert descriptors[0].transports == [
        AuthenticatorTransport.HYBRID,
        AuthenticatorTransport.BLE,
    ]
    assert descriptors[1].id == credential_2.credential_id
    # Made up transport is not a real transport, so it should be ignored.
    assert descriptors[1].transports == [AuthenticatorTransport.INTERNAL]


class SampleWebAuthnTestHelper(WebAuthnHelper):
    pass


def test_credential_get_helper_imports_from_settings(settings, rf):
    """Test that the get_webauthn_helper methods imports a class set in settings."""

    settings.OTP_WEBAUTHN_HELPER_CLASS = (
        "tests.unit.test_models.SampleWebAuthnTestHelper"
    )

    request = rf.get("/")

    helper = WebAuthnCredential.get_webauthn_helper(request)
    assert isinstance(helper, SampleWebAuthnTestHelper)


def test_credential_get_helper_imports_from_settings__not_importable(settings, rf):
    """Test that the get_webauthn_helper methods fails when the class set in settings is not importable."""

    settings.OTP_WEBAUTHN_HELPER_CLASS = "foo.bar"

    request = rf.get("/")

    with pytest.raises(ImportError):
        WebAuthnCredential.get_webauthn_helper(request)


def test_user_handle_generate_handle_hex(user_handle_model):
    """Test that the generate_handle_hex method works."""
    handle = user_handle_model.generate_handle()

    assert isinstance(handle, bytes)
    assert len(handle) == 64


@pytest.mark.django_db
def test_user_handle__str__(user_handle):
    """Test that the __str__ method works."""

    handle_str = str(user_handle)

    assert str(user_handle.user) in handle_str
    assert user_handle.handle_hex in handle_str


@pytest.mark.django_db
def test_user_handle_unique(user_handle_model):
    """Test that it is not possible to save duplicate handles."""
    handle = user_handle_model.generate_handle()

    user_handle_model.objects.create(handle_hex=handle.hex(), user=UserFactory())

    with pytest.raises(IntegrityError):
        user_handle_model.objects.create(handle_hex=handle.hex(), user=UserFactory())


@pytest.mark.django_db
def test_user_handle_get_handle_for_user(user, user_handle_model):
    """Test that the get_handle_for_user method works and creates if a handle if none exists."""
    assert user_handle_model.objects.count() == 0
    handle = WebAuthnUserHandle.get_handle_for_user(user)
    assert isinstance(handle, bytes)
    assert len(handle) == 64
    assert user_handle_model.objects.count() == 1

    # After initial creation, the same handle should be returned.
    handle_2 = WebAuthnUserHandle.get_handle_for_user(user)
    assert handle == handle_2

    # And different users should have different handles.
    handle_other_user = WebAuthnUserHandle.get_handle_for_user(UserFactory())
    assert handle != handle_other_user


@pytest.mark.django_db
def test_user_handle_get_user_by_handle(user, user_handle_model):
    """Test that the get_handle_by_user method works."""
    handle = WebAuthnUserHandle.get_handle_for_user(user)

    assert WebAuthnUserHandle.get_user_by_handle(handle) == user
    assert WebAuthnUserHandle.get_user_by_handle(b"non_existent_handle") is None
