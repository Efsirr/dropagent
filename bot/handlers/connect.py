"""Telegram handlers for connecting user-owned external service keys."""

from __future__ import annotations

import shlex
from typing import Optional

from agent.integrations import (
    credential_fields_for_integration,
    get_integration_spec,
    integration_secret_hint,
    normalize_integration_credentials,
    serialize_integration_credentials,
)
from agent.secrets import SecretBoxError, seal_secret
from db.service import (
    UserProfile,
    delete_user_integration_secret,
    list_user_integration_credentials,
    save_user_integration_secret,
)
from db.session import get_database_url, get_session
from i18n import t


def handle_connect_command(
    text: str,
    env: Optional[dict] = None,
    user_profile: Optional[UserProfile] = None,
    app_secret: Optional[str] = None,
    lang: Optional[str] = None,
) -> str:
    """Save one user-owned API key in encrypted form."""
    if user_profile is None:
        return f"{t('common.error', lang=lang)}: {t('common.user_not_available', lang=lang)}"

    parts = shlex.split(text.strip())
    if len(parts) == 1:
        return t("common.connect_usage", lang=lang)
    if len(parts) == 2:
        integration_id = parts[1].lower()
        spec = get_integration_spec(integration_id)
        if spec is None:
            return f"{t('common.error', lang=lang)}: {t('common.unsupported_service', lang=lang)}"
        field_specs = credential_fields_for_integration(integration_id)
        if len(field_specs) > 1:
            required = " ".join(
                f"<{field.key}>"
                for field in field_specs
                if field.required
            )
            return (
                t("common.service_info", lang=lang, label=spec.label, value=spec.value, id=integration_id)
                + f"\nUsage: /connect {integration_id} {required}"
            )
        return t("common.service_info", lang=lang, label=spec.label, value=spec.value, id=integration_id)

    integration_id = parts[1].lower()
    spec = get_integration_spec(integration_id)
    if spec is None:
        return f"{t('common.error', lang=lang)}: {t('common.unsupported_service', lang=lang)}"

    field_specs = credential_fields_for_integration(integration_id)
    payload_values = parts[2:]
    credentials_input = None
    api_key = None

    if len(field_specs) <= 1:
        api_key = payload_values[0].strip() if payload_values else ""
    else:
        required_fields = [field for field in field_specs if field.required]
        if len(payload_values) < len(required_fields):
            required = " ".join(f"<{field.key}>" for field in required_fields)
            return f"Usage: /connect {integration_id} {required}"
        credentials_input = {}
        for index, field in enumerate(field_specs):
            if index >= len(payload_values):
                break
            credentials_input[field.key] = payload_values[index].strip()

    secret = app_secret if app_secret is not None else (env or {}).get("APP_SECRET_KEY", "")
    try:
        normalized_credentials = normalize_integration_credentials(
            integration_id,
            api_key=api_key,
            credentials=credentials_input,
        )
        encrypted_secret = seal_secret(
            serialize_integration_credentials(normalized_credentials),
            app_secret=secret,
        )
    except (SecretBoxError, ValueError):
        return t("common.key_save_failed", lang=lang)

    session = get_session(get_database_url(env))
    try:
        saved = save_user_integration_secret(
            session,
            telegram_chat_id=user_profile.telegram_chat_id,
            integration_id=integration_id,
            encrypted_secret=encrypted_secret,
            secret_hint=integration_secret_hint(integration_id, normalized_credentials),
        )
    finally:
        session.close()

    return t("common.service_connected", lang=lang, label=spec.label, hint=saved.secret_hint)


def handle_disconnect_command(
    text: str,
    env: Optional[dict] = None,
    user_profile: Optional[UserProfile] = None,
    lang: Optional[str] = None,
) -> str:
    """Remove a connected service key for the current user."""
    if user_profile is None:
        return f"{t('common.error', lang=lang)}: {t('common.user_not_available', lang=lang)}"

    parts = text.strip().split(maxsplit=1)
    if len(parts) != 2:
        return t("common.disconnect_usage", lang=lang)

    integration_id = parts[1].strip().lower()
    spec = get_integration_spec(integration_id)
    if spec is None:
        return f"{t('common.error', lang=lang)}: {t('common.unsupported_service', lang=lang)}"

    session = get_session(get_database_url(env))
    try:
        delete_user_integration_secret(
            session,
            telegram_chat_id=user_profile.telegram_chat_id,
            integration_id=integration_id,
        )
        remaining = list_user_integration_credentials(
            session,
            telegram_chat_id=user_profile.telegram_chat_id,
        )
    finally:
        session.close()

    return t("common.service_disconnected", lang=lang, label=spec.label, remaining=len(remaining))
