"""Config and options flow for rmbt_nettest."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    CLIENT_VERSION,
    CONF_DURATION,
    CONF_HOST,
    CONF_NO_TLS_VERIFY,
    CONF_SCAN_INTERVAL,
    CONF_THREADS,
    CONF_UUID,
    DEFAULT_DURATION,
    DEFAULT_HOST,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_THREADS,
    DOMAIN,
    LOGGER,
)


def _normalise_host(host: str) -> str:
    if not host.startswith(("http://", "https://")):
        host = "https://" + host
    return host.rstrip("/")


def _register_client(host: str) -> str:
    """Call request_settings to verify connectivity and obtain a UUID."""
    from rmbt_nettest import control  # noqa: PLC0415
    return control.request_settings(host, None, CLIENT_VERSION, False)


class RmbtSpeedTestConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the initial setup config flow."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> RmbtSpeedTestOptionsFlow:
        return RmbtSpeedTestOptionsFlow()

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = _normalise_host(user_input[CONF_HOST])
            try:
                uuid = await self.hass.async_add_executor_job(_register_client, host)
            except Exception as err:
                LOGGER.warning("Cannot connect to RMBT control server %s: %s", host, err)
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(host)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=host,
                    data={CONF_HOST: host, CONF_UUID: uuid},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST, default=DEFAULT_HOST): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.URL),
                ),
            }),
            errors=errors,
        )


class RmbtSpeedTestOptionsFlow(config_entries.OptionsFlow):
    """Handle options (test interval, threads, duration)."""

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        opts = self.config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=opts.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=15, max=1440, step=15,
                        unit_of_measurement="min",
                        mode=selector.NumberSelectorMode.SLIDER,
                    ),
                ),
                vol.Optional(
                    CONF_THREADS,
                    default=opts.get(CONF_THREADS, DEFAULT_THREADS),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0, max=8, step=1,
                        mode=selector.NumberSelectorMode.BOX,
                    ),
                ),
                vol.Optional(
                    CONF_DURATION,
                    default=opts.get(CONF_DURATION, DEFAULT_DURATION),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0, max=30, step=1,
                        unit_of_measurement="s",
                        mode=selector.NumberSelectorMode.BOX,
                    ),
                ),
                vol.Optional(
                    CONF_NO_TLS_VERIFY,
                    default=opts.get(CONF_NO_TLS_VERIFY, False),
                ): selector.BooleanSelector(),
            }),
        )
