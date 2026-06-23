"""Home Assistant integration for RMBT network speed tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import homeassistant.helpers.config_validation as cv
from homeassistant.const import Platform

from .const import DOMAIN, LOGGER
from .coordinator import RmbtSpeedTestCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.SENSOR]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


def _check_c_extension() -> None:
    """Warn once if the GIL-free C extension is not available."""
    try:
        from rmbt_client import rmbt_loop  # noqa: F401
    except ImportError:
        LOGGER.warning(
            "[Warn] rmbt_loop C extension not available — using pure-Python fallback. "
            "Throughput on multi-threaded tests may be limited by the GIL. "
            "A pre-built wheel for your platform may not yet be published to PyPI; "
            "see https://github.com/raaaimund/open-rmbt-client-cli for details."
        )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _check_c_extension()
    coordinator = RmbtSpeedTestCoordinator(hass, entry)
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    # Run the first test in the background so setup doesn't block HA startup.
    hass.async_create_task(coordinator.async_refresh(), eager_start=False)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
