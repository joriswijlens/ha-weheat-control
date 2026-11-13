"""Number: standing hot water target temperature."""

from __future__ import annotations

from homeassistant.components.number import NumberDeviceClass, NumberEntity
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import WeheatControlConfigEntry
from .entity import WeheatControlEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: WeheatControlConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([DhwTargetNumber(entry.runtime_data)])


class DhwTargetNumber(WeheatControlEntity, NumberEntity):
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_min_value = 40
    _attr_native_max_value = 60
    _attr_native_step = 1

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "dhw_target_temperature")

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.dhw_target_temperature

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_write({"DhwTargetTemperature": int(value)})
