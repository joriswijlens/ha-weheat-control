from unittest.mock import patch

import pytest
import requests
from homeassistant.config_entries import ConfigEntryState
from homeassistant.exceptions import HomeAssistantError
from weheat_control import ApiException

from custom_components.weheat_control.const import DOMAIN

C = "custom_components.weheat_control.coordinator"


async def setup(hass, entry):
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_setup_creates_entities(hass, entry, login, pump):
    await setup(hass, entry)
    assert entry.state is ConfigEntryState.LOADED
    assert hass.states.get("switch.weheat_heat_pump_hot_water_schedule").state == "on"
    assert hass.states.get("number.weheat_heat_pump_hot_water_target_temperature").state == "50"


async def test_switch_and_number_write(hass, entry, login, pump):
    await setup(hass, entry)
    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": "switch.weheat_heat_pump_hot_water_schedule"}, blocking=True
    )
    pump.async_set_settings.assert_awaited_with("tok", {"DhwScheduleEnabled": 0})
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": "number.weheat_heat_pump_hot_water_target_temperature", "value": 55},
        blocking=True,
    )
    pump.async_set_settings.assert_awaited_with("tok", {"DhwTargetTemperature": 55})


async def test_boost_service(hass, entry, login, pump):
    await setup(hass, entry)
    await hass.services.async_call(DOMAIN, "boost_dhw", {"minutes": 30}, blocking=True)
    pump.async_boost_dhw.assert_awaited_with("tok", minutes=30)
    await hass.services.async_call(DOMAIN, "boost_dhw", {}, blocking=True)
    pump.async_boost_dhw.assert_awaited_with("tok", minutes=60)


async def test_write_failure_is_a_service_error(hass, entry, login, pump):
    await setup(hass, entry)
    pump.async_boost_dhw.side_effect = ApiException(500, "boom")
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(DOMAIN, "boost_dhw", {}, blocking=True)


async def test_unload_removes_service(hass, entry, login, pump):
    await setup(hass, entry)
    await hass.config_entries.async_unload(entry.entry_id)
    assert not hass.services.has_service(DOMAIN, "boost_dhw")


async def test_bad_credentials_start_reauth(hass, entry):
    with patch(f"{C}.login", side_effect=RuntimeError("login rejected")):
        await setup(hass, entry)
    assert entry.state is ConfigEntryState.SETUP_ERROR
    assert any(hass.config_entries.flow.async_progress_by_handler(DOMAIN))


async def test_portal_down_retries(hass, entry):
    with patch(f"{C}.login", side_effect=requests.ConnectionError):
        await setup(hass, entry)
    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_unauthorized_settings_start_reauth(hass, entry, login, pump):
    pump.async_get_settings.side_effect = ApiException(401, "")
    await setup(hass, entry)
    assert entry.state is ConfigEntryState.SETUP_ERROR
    assert any(hass.config_entries.flow.async_progress_by_handler(DOMAIN))
