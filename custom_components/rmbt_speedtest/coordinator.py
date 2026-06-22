"""DataUpdateCoordinator for rmbt_speedtest."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CLIENT_VERSION,
    CONF_DURATION,
    CONF_HOST,
    CONF_NO_TLS_VERIFY,
    CONF_SCAN_INTERVAL,
    CONF_THREADS,
    CONF_UUID,
    DEFAULT_DURATION,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_THREADS,
    DOMAIN,
    LOGGER,
)
from .data import SpeedTestResult
from .runner import run_speedtest

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant


class RmbtSpeedTestCoordinator(DataUpdateCoordinator[SpeedTestResult | None]):
    """Runs RMBT speed tests on a schedule and distributes results to entities."""

    config_entry: ConfigEntry
    running: bool

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        self.running = False
        interval = config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            config_entry=config_entry,
            update_interval=timedelta(minutes=interval),
            always_update=True,
        )

    async def _async_update_data(self) -> SpeedTestResult:
        host = self.config_entry.data[CONF_HOST]
        uuid = self.config_entry.data.get(CONF_UUID)
        threads = int(self.config_entry.options.get(CONF_THREADS, DEFAULT_THREADS))
        duration = int(self.config_entry.options.get(CONF_DURATION, DEFAULT_DURATION))
        no_tls_verify = bool(self.config_entry.options.get(CONF_NO_TLS_VERIFY, False))

        self.running = True
        self.async_update_listeners()

        try:
            raw = await self.hass.async_add_executor_job(
                run_speedtest, host, uuid, threads, duration, no_tls_verify, CLIENT_VERSION,
            )
        except Exception as err:
            raise UpdateFailed(f"Speed test failed: {err}") from err
        finally:
            self.running = False

        if raw["uuid"] != uuid:
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={**self.config_entry.data, CONF_UUID: raw["uuid"]},
            )

        return SpeedTestResult(
            download_mbps=raw["download_mbps"],
            upload_mbps=raw["upload_mbps"],
            ping_min_ms=raw["ping_min_ms"],
            ping_median_ms=raw["ping_median_ms"],
            ping_count=raw["ping_count"],
            result_url=raw.get("result_url"),
            test_uuid=raw.get("test_uuid"),
            open_test_uuid=raw.get("open_test_uuid"),
        )
