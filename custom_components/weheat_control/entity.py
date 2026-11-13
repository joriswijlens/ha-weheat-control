"""Shared base entity."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import WeheatControlCoordinator


class WeheatControlEntity(CoordinatorEntity[WeheatControlCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: WeheatControlCoordinator, key: str) -> None:
        super().__init__(coordinator)
        board = coordinator.info.control_board_id
        self._attr_unique_id = f"{board}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, board)},
            name="Weheat heat pump",
            manufacturer="Weheat",
            serial_number=coordinator.info.serial_number,
        )
