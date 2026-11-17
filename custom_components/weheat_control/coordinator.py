"""Token handling and polling of the Weheat settings."""

from __future__ import annotations

import logging

import requests
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from weheat_control import (
    DEFAULT_HOST,
    ApiException,
    HeatPumpSettings,
    InstallationDiscovery,
    InstallationSettingsDto,
    PortalSession,
)

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
        self._session: PortalSession | None = None

    async def async_access_token(self) -> str:
        """A valid access token: cached, renewed from the portal session, or a new login."""
        if self._session is None:
            self._session = PortalSession()
        data = self.config_entry.data
        try:
            return await self.hass.async_add_executor_job(
                self._session.access_token, data[CONF_USERNAME], data[CONF_PASSWORD]
            )
        except requests.RequestException as err:
            raise UpdateFailed(f"cannot reach the Weheat portal: {err}") from err
        except RuntimeError as err:
            raise ConfigEntryAuthFailed(str(err)) from err

    async def async_setup(self) -> None:
        """Find the heat pump; called once before the first refresh."""
        try:
            token = await self.async_access_token()
            session = async_get_clientsession(self.hass)
            found = await InstallationDiscovery.async_discover(DEFAULT_HOST, token, session)
        except UpdateFailed as err:
            raise ConfigEntryNotReady(str(err)) from err
        except ApiException as err:
            raise self._api_error(err, ConfigEntryNotReady) from err
        if not found:
            raise ConfigEntryNotReady("no heat pump with a control board on this account")
        self.info = found[0]
        self.pump = HeatPumpSettings(
            DEFAULT_HOST, self.info.installation_id, self.info.control_board_id, session
        )

    @staticmethod
    def _api_error(err: ApiException, other: type[Exception]) -> Exception:
        """401/403 mean the credentials no longer work; anything else is transient."""
        if err.status in (401, 403):
            return ConfigEntryAuthFailed(str(err))
        return other(str(err))

    async def _async_update_data(self) -> InstallationSettingsDto:
        try:
            return await self.pump.async_get_settings(await self.async_access_token())
        except ApiException as err:
            raise self._api_error(err, UpdateFailed) from err

    async def async_write(self, settings: dict) -> None:
        """Write raw PascalCase settings, then re-read."""
        try:
            await self.pump.async_set_settings(await self.async_access_token(), settings)
        except (ApiException, UpdateFailed) as err:
            raise HomeAssistantError(f"Weheat rejected the change: {err}") from err
        await self.async_request_refresh()
