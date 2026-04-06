"""Config flow for Modbus integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME

from .const import DEFAULT_HUB, DOMAIN


class ModbusFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle Modbus config flow (YAML import only)."""

    VERSION = 1

    async def async_step_import(self, import_config: dict) -> ConfigFlowResult:
        """Import configuration from YAML."""
        hub_name = import_config.get(CONF_NAME, DEFAULT_HUB)
        await self.async_set_unique_id(hub_name)
        self._abort_if_unique_id_configured(updates=import_config)
        return self.async_create_entry(title=hub_name, data=import_config)
