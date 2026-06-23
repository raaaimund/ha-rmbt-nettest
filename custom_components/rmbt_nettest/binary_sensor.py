"""Binary sensor platform for rmbt_nettest — exposes test-running state."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_HOST, DOMAIN
from .coordinator import RmbtSpeedTestCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

PARALLEL_UPDATES = 0

_DESCRIPTION = BinarySensorEntityDescription(
    key="test_running",
    translation_key="test_running",
    icon="mdi:speedometer",
    has_entity_name=True,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: RmbtSpeedTestCoordinator = entry.runtime_data
    async_add_entities([RmbtTestRunningSensor(coordinator)])


class RmbtTestRunningSensor(CoordinatorEntity[RmbtSpeedTestCoordinator], BinarySensorEntity):
    """On while a speed test is in progress, off otherwise."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: RmbtSpeedTestCoordinator) -> None:
        super().__init__(coordinator)
        self.entity_description = _DESCRIPTION
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_test_running"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name=coordinator.config_entry.title,
            model="RMBT Client",
            configuration_url=coordinator.config_entry.data[CONF_HOST],
        )

    @property
    def available(self) -> bool:
        return True

    @property
    def is_on(self) -> bool:
        return self.coordinator.running
