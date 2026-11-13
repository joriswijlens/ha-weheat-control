from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.weheat_control.const import DOMAIN

C = "custom_components.weheat_control.coordinator"
TOKENS = {"access_token": "tok", "refresh_token": "ref", "expires_in": 300}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture
def entry():
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id="a@b.nl",
        data={CONF_USERNAME: "a@b.nl", CONF_PASSWORD: "pw"},
    )


@pytest.fixture
def login():
    with patch(f"{C}.login", return_value=dict(TOKENS)) as m:
        yield m


@pytest.fixture
def pump():
    settings = SimpleNamespace(dhw_target_temperature=50, dhw_schedule_enabled=1)
    info = SimpleNamespace(
        installation_id="inst", control_board_id="board", serial_number="SN1"
    )
    instance = MagicMock()
    instance.async_get_settings = AsyncMock(return_value=settings)
    instance.async_set_settings = AsyncMock()
    instance.async_boost_dhw = AsyncMock()
    with (
        patch(f"{C}.InstallationDiscovery.async_discover", AsyncMock(return_value=[info])),
        patch(f"{C}.HeatPumpSettings", return_value=instance),
    ):
        yield instance
