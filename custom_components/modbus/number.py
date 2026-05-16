"""Support for Modbus number entities (holding register read/write)."""

from __future__ import annotations

import struct
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode, RestoreNumber
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_NAME,
    CONF_UNIT_OF_MEASUREMENT,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import get_hub
from .const import (
    _LOGGER,
    CALL_TYPE_REGISTER_HOLDING,
    CALL_TYPE_WRITE_REGISTER,
    CONF_DATA_TYPE,
    CONF_MAX_VALUE,
    CONF_MIN_VALUE,
    CONF_NUMBERS,
    CONF_PRECISION,
    CONF_SCALE,
    DEFAULT_OFFSET,
    DEFAULT_SCALE,
    DOMAIN,
)
from .entity import ModbusStructEntity
from .modbus import ModbusHub

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Modbus number entities from a config entry."""
    conf_hub = hass.data[DOMAIN][config_entry.entry_id]
    if not (numbers := conf_hub.get(CONF_NUMBERS)):
        return
    hub = get_hub(hass, conf_hub[CONF_NAME])
    async_add_entities(ModbusNumberEntity(hass, hub, cfg) for cfg in numbers)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up Modbus number entities from YAML (legacy)."""
    if discovery_info is None or not (numbers := discovery_info.get(CONF_NUMBERS)):
        return
    hub = get_hub(hass, discovery_info[CONF_NAME])
    async_add_entities(ModbusNumberEntity(hass, hub, cfg) for cfg in numbers)


class ModbusNumberEntity(ModbusStructEntity, RestoreNumber):
    """Represents a Modbus holding-register as a NumberEntity."""

    def __init__(self, hass: HomeAssistant, hub: ModbusHub, config: dict) -> None:
        """Initialize the number entity."""
        config.setdefault("input_type", CALL_TYPE_REGISTER_HOLDING)
        super().__init__(hass, hub, config)
        self._attr_native_min_value = float(config.get(CONF_MIN_VALUE, 0))
        self._attr_native_max_value = float(config.get(CONF_MAX_VALUE, 100))
        step = config.get("step", None)
        if step is not None:
            self._attr_native_step = float(step)
        else:
            precision = config.get(CONF_PRECISION, 1)
            self._attr_native_step = 10 ** (-precision) if precision > 0 else 1.0
        self._attr_native_unit_of_measurement = config.get(CONF_UNIT_OF_MEASUREMENT)
        self._attr_mode = NumberMode.BOX
        self._attr_native_value: float | None = None
        self._scale = float(config.get(CONF_SCALE, DEFAULT_SCALE))
        self._precision = int(config.get(CONF_PRECISION, 1))

    async def async_added_to_hass(self) -> None:
        """Restore last state on startup."""
        await self.async_base_added_to_hass()
        if last_number_data := await self.async_get_last_number_data():
            self._attr_native_value = last_number_data.native_value
        await super().async_added_to_hass()

    async def async_set_native_value(self, value: float) -> None:
        """Write value to the Modbus holding register."""
        raw = round(value / self._scale) if self._scale else int(value)
        result = await self._hub.async_pb_call(
            self._device_address,
            self._address,
            int(raw),
            CALL_TYPE_WRITE_REGISTER,
        )
        if result is None:
            self._attr_available = False
            self.async_write_ha_state()
            return
        self._attr_available = True
        self._attr_native_value = round(value, self._precision)
        self.async_write_ha_state()

    async def _async_update(self) -> None:
        """Read value from Modbus register."""
        result = await self._hub.async_pb_call(
            self._device_address,
            self._address,
            self._count,
            CALL_TYPE_REGISTER_HOLDING,
        )
        if result is None:
            self._attr_available = False
            return
        self._attr_available = True
        raw = result.registers[0]
        self._attr_native_value = round(raw * self._scale, self._precision)
