from unittest.mock import patch

import requests
from homeassistant.config_entries import SOURCE_USER
from homeassistant.data_entry_flow import FlowResultType

from custom_components.weheat_control.const import DOMAIN

CF = "custom_components.weheat_control.config_flow.login"
CREDS = {"username": "A@b.nl", "password": "pw"}


async def test_user_flow(hass, login, pump):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    with patch(CF):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], CREDS)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "A@b.nl"


async def test_user_flow_errors_then_recovers(hass):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    with patch(CF, side_effect=RuntimeError("login rejected")):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], CREDS)
    assert result["errors"] == {"base": "invalid_auth"}
    with patch(CF, side_effect=requests.ConnectionError):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], CREDS)
    assert result["errors"] == {"base": "cannot_connect"}


async def test_duplicate_account_aborts(hass, entry):
    entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], CREDS)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_reauth_updates_password(hass, entry, login, pump):
    entry.add_to_hass(hass)
    result = await entry.start_reauth_flow(hass)
    assert result["step_id"] == "reauth_confirm"
    with patch(CF, side_effect=RuntimeError("login rejected")):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"password": "bad"}
        )
    assert result["errors"] == {"base": "invalid_auth"}
    with patch(CF):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"password": "new"}
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data["password"] == "new"
    assert entry.data["username"] == "a@b.nl"
