from django_otp_webauthn.urls import urlpatterns as otp_webauthn_urls


def test_urls__js_i18n_catalog():
    """Verify that the js-i18n-catalog URL is present in the otp_webauthn URLs."""

    url_pattern_found = False
    for urlpattern in otp_webauthn_urls:
        if urlpattern.name == "js-i18n-catalog":
            url_pattern_found = True
    assert url_pattern_found, "js-i18n-catalog URL not found"
