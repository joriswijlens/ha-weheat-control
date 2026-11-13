"""Switch: hot water schedule on/off."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import WeheatControlConfigEntry
from .entity import WeheatControlEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: WeheatControlConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([DhwScheduleSwitch(entry.runtime_data)])


class DhwScheduleSwitch(WeheatControlEntity, SwitchEntity):
    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "dhw_schedule")

    @property
    def is_on(self) -> bool | None:
        value = self.coordinator.data.dhw_schedule_enabled
        return None if value is None else bool(value)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_write({"DhwScheduleEnabled": 1})

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_write({"DhwScheduleEnabled": 0})
