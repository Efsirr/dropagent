"""Tests for per-user integration credential metadata."""

from datetime import datetime, timezone

from agent.secrets import mask_secret, seal_secret
from db.service import (
    delete_user_integration_secret,
    get_user_integration_encrypted_secret,
    list_user_integration_credentials,
    mark_user_integration_checked,
    save_user_integration_secret,
)
from db.session import get_database_url, get_session


class TestUserIntegrationCredentials:
    def test_save_list_and_delete_user_integration_secret(self, tmp_path):
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'integrations.db'}"}
        app_secret = "dev-secret-with-enough-length"
        session = get_session(get_database_url(env))
        try:
            encrypted = seal_secret("keepa-api-key-123", app_secret=app_secret)

            saved = save_user_integration_secret(
                session,
                telegram_chat_id="100",
                integration_id="keepa",
                encrypted_secret=encrypted,
                secret_hint=mask_secret("keepa-api-key-123"),
            )
            listed = list_user_integration_credentials(session, "100")
            stored = get_user_integration_encrypted_secret(session, "100", "keepa")
            remaining = delete_user_integration_secret(session, "100", "keepa")

            assert saved.integration_id == "keepa"
            assert saved.secret_hint == "keepa-...-123"
            assert saved.status == "connected"
            assert listed == [saved]
            assert stored == encrypted
            assert "keepa-api-key-123" not in repr(listed)
            assert encrypted not in repr(listed)
            assert remaining == []
        finally:
            session.close()

    def test_save_updates_existing_integration(self, tmp_path):
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'integrations.db'}"}
        session = get_session(get_database_url(env))
        try:
            first = save_user_integration_secret(
                session,
                telegram_chat_id="100",
                integration_id="keepa",
                encrypted_secret="encrypted-one",
                secret_hint="one",
            )
            second = save_user_integration_secret(
                session,
                telegram_chat_id="100",
                integration_id="keepa",
                encrypted_secret="encrypted-two",
                secret_hint="two",
            )
            listed = list_user_integration_credentials(session, "100")

            assert second.credential_id == first.credential_id
            assert second.secret_hint == "two"
            assert listed == [second]
        finally:
            session.close()

    def test_mark_checked_updates_status(self, tmp_path):
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'integrations.db'}"}
        checked_at = datetime(2026, 1, 2, tzinfo=timezone.utc)
        session = get_session(get_database_url(env))
        try:
            save_user_integration_secret(
                session,
                telegram_chat_id="100",
                integration_id="keepa",
                encrypted_secret="encrypted",
                secret_hint="kee...123",
            )

            checked = mark_user_integration_checked(
                session,
                telegram_chat_id="100",
                integration_id="keepa",
                status="needs_attention",
                checked_at=checked_at,
            )

            assert checked is not None
            assert checked.status == "needs_attention"
            assert checked.last_checked_at == checked_at
        finally:
            session.close()

    def test_users_are_isolated(self, tmp_path):
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'integrations.db'}"}
        session = get_session(get_database_url(env))
        try:
            save_user_integration_secret(
                session,
                telegram_chat_id="100",
                integration_id="keepa",
                encrypted_secret="user-100-secret",
                secret_hint="100",
            )
            save_user_integration_secret(
                session,
                telegram_chat_id="200",
                integration_id="keepa",
                encrypted_secret="user-200-secret",
                secret_hint="200",
            )

            user_100 = list_user_integration_credentials(session, "100")
            user_200 = list_user_integration_credentials(session, "200")

            assert user_100[0].secret_hint == "100"
            assert user_200[0].secret_hint == "200"
            assert get_user_integration_encrypted_secret(session, "100", "keepa") == "user-100-secret"
        finally:
            session.close()
