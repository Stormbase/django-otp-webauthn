import pytest


@pytest.mark.django_db
def test_wellknown_webauthn__origins(client, settings):
    settings.OTP_WEBAUTHN_RP_RELATED_ORIGINS = ["https://example.com"]
    """Verify that the well-known endpoint returns the allowed origins."""
    response = client.get("/.well-known/webauthn")
    assert response.status_code == 200

    assert response["Content-Type"] == "application/json"
    data = response.json()
    assert "origins" in data
    assert data["origins"] == ["https://example.com"]
    assert "Cache-Control" in response
    assert "public" in response["Cache-Control"]
