import factory
import factory.fuzzy
from factory.random import randgen as factory_randgen

from django_otp_webauthn.models import WebAuthnAttestation, WebAuthnCredential

from .fuzzy import FuzzyBytes


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "auth.User"
        django_get_or_create = ["username"]

    username = factory.Faker("user_name")
    email = factory.Faker("email")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")


class WebAuthnCredentialFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WebAuthnCredential
        django_get_or_create = ["credential_id"]

    class Params:
        attested = factory.Trait(
            attestation=factory.SubFactory("tests.factories.WebAuthnAttestationFactory")
        )

    @factory.lazy_attribute
    def name(self):
        return f"{self.user.username}'s credential"

    user = factory.SubFactory("tests.factories.UserFactory")
    credential_id = FuzzyBytes()
    sign_count = 0
    discoverable = factory.fuzzy.FuzzyChoice([True, False, None])
    aaguid = factory.Faker("uuid4")
    public_key = b"\00"
    transports = factory.fuzzy.FuzzyChoice(
        [
            ["usb"],
            ["nfc"],
            ["ble"],
            ["usb", "nfc"],
            ["usb", "ble"],
            ["nfc", "ble"],
            ["usb", "nfc", "ble"],
        ]
    )
    backup_eligible = factory.fuzzy.FuzzyChoice([True, False])

    @factory.lazy_attribute
    def backup_state(self):
        # If backup_eligible is True, backup_state could be True or False.
        # If backup_eligible is False, backup_state should also always be False.
        return factory_randgen.choice([True, False]) if self.backup_eligible else False


class WebAuthnAttestationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WebAuthnAttestation
        django_get_or_create = ["credential"]

    credential = factory.SubFactory("tests.factories.WebAuthnCredentialFactory")

    # We can't easily generate these fields, so we just set them to empty values.
    fmt = "none"
    data = b"\00"
    client_data_json = b"\00"
