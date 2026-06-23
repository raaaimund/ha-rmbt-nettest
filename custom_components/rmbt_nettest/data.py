"""Runtime data types for rmbt_nettest."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

    from .coordinator import RmbtSpeedTestCoordinator

type RmbtSpeedTestConfigEntry = ConfigEntry[RmbtSpeedTestCoordinator]


@dataclass
class SpeedTestResult:
    """Result of one completed RMBT speed test."""

    download_mbps: float
    upload_mbps: float
    ping_min_ms: float
    ping_median_ms: float
    ping_count: int
    result_url: str | None
    test_uuid: str | None
    open_test_uuid: str | None
