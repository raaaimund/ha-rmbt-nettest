"""Button platform for rmbt_speedtest — triggers an immediate test."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_HOST, DOMAIN
from .coordinator import RmbtSpeedTestCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

PARALLEL_UPDATES = 1

_BUTTON_DESCRIPTION = ButtonEntityDescription(
    key="run_test",
    translation_key="run_test",
    icon="mdi:speedometer",
    has_entity_name=True,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: RmbtSpeedTestCoordinator = entry.runtime_data
    async_add_entities([RmbtRunTestButton(coordinator)])


class RmbtRunTestButton(CoordinatorEntity[RmbtSpeedTestCoordinator], ButtonEntity):
    """Button that kicks off an on-demand speed test."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: RmbtSpeedTestCoordinator) -> None:
        super().__init__(coordinator)
        self.entity_description = _BUTTON_DESCRIPTION
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_run_test"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name=coordinator.config_entry.title,
            manufacturer="RTR",
            model="RMBT Client",
            configuration_url=coordinator.config_entry.data.get(CONF_HOST),
        )

    async def async_press(self) -> None:
        await self.coordinator.async_request_refresh()
