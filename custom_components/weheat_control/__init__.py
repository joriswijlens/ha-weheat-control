"""Write access to a Weheat heat pump (DHW schedule, target, boost)."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
import homeassistant.helpers.config_validation as cv

from .const import ATTR_MINUTES, DOMAIN, PLATFORMS, SERVICE_BOOST_DHW
from .coordinator import WeheatControlConfigEntry, WeheatControlCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: WeheatControlConfigEntry) -> bool:
    coordinator = WeheatControlCoordinator(hass, entry)
    await coordinator.async_setup()
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    async def boost_dhw(call: ServiceCall) -> None:
        entries = hass.config_entries.async_loaded_entries(DOMAIN)
        if not entries:
            raise ServiceValidationError("Weheat Control is not set up")
        await entries[0].runtime_data.async_boost_dhw(call.data[ATTR_MINUTES])

    if not hass.services.has_service(DOMAIN, SERVICE_BOOST_DHW):
        hass.services.async_register(
            DOMAIN,
            SERVICE_BOOST_DHW,
            boost_dhw,
            schema=vol.Schema(
                {vol.Optional(ATTR_MINUTES, default=60): vol.All(cv.positive_int, vol.Range(max=720))}
            ),
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: WeheatControlConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded and not hass.config_entries.async_loaded_entries(DOMAIN):
        hass.services.async_remove(DOMAIN, SERVICE_BOOST_DHW)
    return unloaded
