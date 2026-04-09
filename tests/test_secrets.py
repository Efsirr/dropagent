"""Tests for user-owned API key sealing."""

import pytest

from agent.secrets import SecretBoxError, mask_secret, open_secret, seal_secret


class TestSecretBox:
    def test_seals_and_opens_secret(self):
        app_secret = "dev-secret-with-enough-length"
        sealed = seal_secret("keepa-api-key-123", app_secret=app_secret)

        assert sealed != "keepa-api-key-123"
        assert sealed.startswith("da1.")
        assert open_secret(sealed, app_secret=app_secret) == "keepa-api-key-123"

    def test_wrong_app_secret_fails(self):
        sealed = seal_secret(
            "keepa-api-key-123",
            app_secret="dev-secret-with-enough-length",
        )

        with pytest.raises(SecretBoxError):
            open_secret(sealed, app_secret="different-secret-with-length")

    def test_rejects_short_app_secret(self):
        with pytest.raises(SecretBoxError):
            seal_secret("api-key", app_secret="short")

    def test_masks_secret(self):
        assert mask_secret("keepa-api-key-123") == "keepa-...-123"
        assert mask_secret("12345678") == "12...78"
        assert mask_secret("") == ""
