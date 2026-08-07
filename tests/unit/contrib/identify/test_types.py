from typing import Literal

import pytest
from bs4 import BeautifulSoup
from identify_passkey import PASSKEYS, identify_passkey

from django_otp_webauthn.contrib.identify import (
    identify_passkey as get_passkey_descriptor,
)
from django_otp_webauthn.contrib.identify.types import PasskeyDescriptor, PasskeyIcon
from tests.factories import APPLE_AAGUID


def get_icon_descriptor(i, theme: Literal["light", "dark"] = "light"):
    """Helper function to get the icon descriptor for a given passkey index and theme."""
    passkey_descriptor = identify_passkey(list(PASSKEYS.items())[i][0])

    if theme == "light":
        return passkey_descriptor.icon_light
    return passkey_descriptor.icon_dark


def test_passkey_icon():
    """Test that PasskeyIcon correctly wraps the identify_passkey.PasskeyIcon."""
    icon = identify_passkey(APPLE_AAGUID).icon_light
    passkey_icon = PasskeyIcon(ref=icon)

    assert passkey_icon.mime_type == icon.mime_type
    assert passkey_icon.data_uri == icon.data_uri
    assert icon.path.name in passkey_icon.static_url
    assert passkey_icon.data_uri == icon.data_uri
    assert passkey_icon.static_url.endswith(icon.path.name)
    assert passkey_icon.theme == "light"


def test_passkey_descriptor():
    """Test that PasskeyDescriptor correctly wraps the identify_passkey.PasskeyDescriptor."""
    descriptor = identify_passkey(APPLE_AAGUID)
    passkey_descriptor = PasskeyDescriptor(
        aaguid=descriptor.aaguid,
        name=descriptor.name,
        icon_light=PasskeyIcon(ref=descriptor.icon_light)
        if descriptor.icon_light
        else None,
        icon_dark=PasskeyIcon(ref=descriptor.icon_dark)
        if descriptor.icon_dark
        else None,
    )

    assert passkey_descriptor.aaguid == descriptor.aaguid
    assert passkey_descriptor.name == descriptor.name
    assert passkey_descriptor.has_icon

    assert passkey_descriptor.icon_data_uri() == descriptor.icon_light.data_uri
    assert passkey_descriptor.icon_data_uri("light") == descriptor.icon_light.data_uri
    assert passkey_descriptor.icon_data_uri("dark") == descriptor.icon_dark.data_uri

    # Light and dark icons are the same for Apple Passwords, so the data URIs should be the same
    assert passkey_descriptor.icon_data_uri(
        "light"
    ) == passkey_descriptor.icon_data_uri("dark")

    # Check the picture_html method works as expected. In this case, since light
    # and dark are the same, this is optimized to not outputting any <source>
    # tags, just a single <img> tag.
    picture_html = BeautifulSoup(
        passkey_descriptor.picture_html(picture_attrs={"class": "my-classname"}),
        "html.parser",
    )
    assert picture_html.find("picture") is not None
    assert picture_html.find("picture")["class"] == ["my-classname"]

    assert picture_html.find("source") is None
    assert picture_html.find("img")["src"] == passkey_descriptor.icon_light.static_url
    assert picture_html.find("img")["width"] == "32"

    # Replace the dark icon with a different one to test the <source> tag generation
    passkey_descriptor = PasskeyDescriptor(
        aaguid=descriptor.aaguid,
        name=descriptor.name,
        icon_light=PasskeyIcon(ref=descriptor.icon_light)
        if descriptor.icon_light
        else None,
        icon_dark=PasskeyIcon(ref=get_icon_descriptor(0, theme="dark")),
    )

    # Request a width of 48 to test that the img_attrs parameter is respected
    picture_html = BeautifulSoup(
        passkey_descriptor.picture_html(img_attrs={"width": "48"}), "html.parser"
    )
    assert picture_html.find("picture") is not None
    source_light = picture_html.find(
        "source", {"media": "(prefers-color-scheme: light)"}
    )
    assert source_light is not None
    assert source_light["srcset"] == passkey_descriptor.icon_light.static_url

    source_dark = picture_html.find("source", {"media": "(prefers-color-scheme: dark)"})
    assert source_dark is not None
    assert source_dark["srcset"] == passkey_descriptor.icon_dark.static_url

    img = picture_html.find("img")
    assert img is not None
    assert img["src"] == passkey_descriptor.icon_light.static_url
    assert img["width"] == "48"


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_passkey_descriptor_picture_html_with_only_one_icon(theme):
    """Test that PasskeyDescriptor.picture_html() correctly handles cases where only one icon is provided."""
    # Request with only a light icon to test that no <source> tag is generated for dark mode
    descriptor = identify_passkey(APPLE_AAGUID)
    passkey_descriptor = PasskeyDescriptor(
        aaguid=descriptor.aaguid,
        name=descriptor.name,
        icon_light=PasskeyIcon(ref=descriptor.icon_light) if theme == "light" else None,
        icon_dark=PasskeyIcon(ref=descriptor.icon_dark) if theme == "dark" else None,
    )
    picture_html = BeautifulSoup(passkey_descriptor.picture_html(), "html.parser")
    assert picture_html.find("picture") is not None
    assert picture_html.find("source") is not None
    assert picture_html.find("source")["media"] == (
        "(prefers-color-scheme: light)"
        if theme == "light"
        else "(prefers-color-scheme: dark)"
    )
    assert picture_html.find("img")["src"] == (
        passkey_descriptor.icon_light.static_url
        if theme == "light"
        else passkey_descriptor.icon_dark.static_url
    )


def test_passkey_descriptor_icon_data_uri__raise_invalid_theme():
    """Test that PasskeyDescriptor raises a ValueError for an invalid theme."""
    passkey_descriptor = get_passkey_descriptor(APPLE_AAGUID)

    with pytest.raises(
        ValueError, match="Invalid theme: invalid_theme. Must be 'light' or 'dark'."
    ):
        passkey_descriptor.icon_data_uri("invalid_theme")


def test_passkey_descriptor_no_icons():
    """Test that PasskeyDescriptor correctly handles a passkey with no icons."""
    # Use a passkey that has no icons. For this test, we'll use the first passkey in the list.
    passkey_descriptor = get_passkey_descriptor(APPLE_AAGUID)
    pk = PasskeyDescriptor(
        aaguid=passkey_descriptor.aaguid,
        name=passkey_descriptor.name,
        icon_light=None,
        icon_dark=None,
    )

    assert not pk.has_icon

    # The picture_html method should return an empty string since there are no icons
    picture_html = pk.picture_html()
    assert picture_html == ""

    assert pk.icon_data_uri() is None
    assert pk.icon_data_uri("light") is None
    assert pk.icon_data_uri("dark") is None
