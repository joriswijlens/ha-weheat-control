"""Token handling and polling of the Weheat settings."""

from __future__ import annotations

import logging
import time

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from weheat_control import (
    DEFAULT_HOST,
    ApiException,
    HeatPumpSettings,
    InstallationDiscovery,
    InstallationSettingsDto,
    login,
)
from weheat_control.auth import refresh

from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

type WeheatControlConfigEntry = ConfigEntry[WeheatControlCoordinator]


class WeheatControlCoordinator(DataUpdateCoordinator[InstallationSettingsDto]):
    """Owns the portal token and the settings of one heat pump."""

    config_entry: WeheatControlConfigEntry
    pump: HeatPumpSettings
    info: InstallationDiscovery.InstallationInfo

    def __init__(self, hass: HomeAssistant, entry: WeheatControlConfigEntry) -> None:
        super().__init__(
            hass, _LOGGER, config_entry=entry, name=DOMAIN, update_interval=UPDATE_INTERVAL
        )
        self._tokens: dict | None = None

    async def async_access_token(self) -> str:
        """A valid access token; refresh or log in again when it has expired."""
        if self._tokens and self._tokens["expires_at"] > time.time() + 30:
            return self._tokens["access_token"]

        tokens = None
        if self._tokens:
            tokens = await self.hass.async_add_executor_job(refresh, self._tokens)
        if not tokens:
            data = self.config_entry.data
            try:
                tokens = await self.hass.async_add_executor_job(
                    login, data[CONF_USERNAME], data[CONF_PASSWORD]
                )
            except Exception as err:
                raise ConfigEntryAuthFailed(str(err)) from err
        tokens["expires_at"] = time.time() + tokens.get("expires_in", 300)
        self._tokens = tokens
        return tokens["access_token"]

    async def async_setup(self) -> None:
        """Find the heat pump; called once before the first refresh."""
        token = await self.async_access_token()
        session = async_get_clientsession(self.hass)
        found = await InstallationDiscovery.async_discover(DEFAULT_HOST, token, session)
        if not found:
            raise UpdateFailed("no heat pump with a control board on this account")
        self.info = found[0]
        self.pump = HeatPumpSettings(
            DEFAULT_HOST, self.info.installation_id, self.info.control_board_id, session
        )

    async def _async_update_data(self) -> InstallationSettingsDto:
        try:
            return await self.pump.async_get_settings(await self.async_access_token())
        except ApiException as err:
            raise UpdateFailed(str(err)) from err

    async def async_write(self, settings: dict) -> None:
        """Write raw PascalCase settings, then re-read."""
        try:
            await self.pump.async_set_settings(await self.async_access_token(), settings)
        except ApiException as err:
            raise UpdateFailed(str(err)) from err
        await self.async_request_refresh()

    async def async_boost_dhw(self, minutes: int) -> None:
        await self.pump.async_boost_dhw(await self.async_access_token(), minutes=minutes)
        await self.async_request_refresh()
