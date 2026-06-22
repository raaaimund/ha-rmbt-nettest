"""Sensor platform for rmbt_speedtest."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfDataRate, UnitOfTime
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, CONF_HOST, DOMAIN
from .coordinator import RmbtSpeedTestCoordinator
from .data import SpeedTestResult

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

PARALLEL_UPDATES = 0

ENTITY_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="download_speed",
        translation_key="download_speed",
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:download-network",
        suggested_display_precision=1,
        has_entity_name=True,
    ),
    SensorEntityDescription(
        key="upload_speed",
        translation_key="upload_speed",
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:upload-network",
        suggested_display_precision=1,
        has_entity_name=True,
    ),
    SensorEntityDescription(
        key="ping_min",
        translation_key="ping_min",
        native_unit_of_measurement=UnitOfTime.MILLISECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:timer-outline",
        suggested_display_precision=1,
        has_entity_name=True,
    ),
    SensorEntityDescription(
        key="ping_median",
        translation_key="ping_median",
        native_unit_of_measurement=UnitOfTime.MILLISECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:timer-outline",
        suggested_display_precision=1,
        has_entity_name=True,
    ),
    SensorEntityDescription(
        key="result_url",
        translation_key="result_url",
        icon="mdi:open-in-new",
        has_entity_name=True,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities."""
    coordinator: RmbtSpeedTestCoordinator = entry.runtime_data
    async_add_entities(
        RmbtSpeedTestSensor(coordinator, description)
        for description in ENTITY_DESCRIPTIONS
    )


class RmbtSpeedTestSensor(CoordinatorEntity[RmbtSpeedTestCoordinator], SensorEntity):
    """A sensor that exposes one field from the last speed test result."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: RmbtSpeedTestCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name=coordinator.config_entry.title,
            manufacturer="RTR",
            model="RMBT Client",
            configuration_url=coordinator.config_entry.data.get(CONF_HOST),
        )

    @property
    def native_value(self) -> float | str | None:
        if self.coordinator.data is None:
            return None
        data: SpeedTestResult = self.coordinator.data
        match self.entity_description.key:
            case "download_speed":
                return round(data.download_mbps, 2)
            case "upload_speed":
                return round(data.upload_mbps, 2)
            case "ping_min":
                return round(data.ping_min_ms, 2)
            case "ping_median":
                return round(data.ping_median_ms, 2)
            case "result_url":
                return data.result_url
        return None

    @property
    def extra_state_attributes(self) -> dict | None:
        if self.coordinator.data is None or self.entity_description.key != "result_url":
            return None
        data: SpeedTestResult = self.coordinator.data
        return {
            "test_uuid": data.test_uuid,
            "open_test_uuid": data.open_test_uuid,
            "ping_count": data.ping_count,
        }
