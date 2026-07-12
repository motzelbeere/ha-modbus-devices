"""Support for Modbus."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.components.binary_sensor import (
    DEVICE_CLASSES_SCHEMA as BINARY_SENSOR_DEVICE_CLASSES_SCHEMA,
)
from homeassistant.components.cover import (
    DEVICE_CLASSES_SCHEMA as COVER_DEVICE_CLASSES_SCHEMA,
)
from homeassistant.components.sensor import (
    CONF_STATE_CLASS,
    DEVICE_CLASSES_SCHEMA as SENSOR_DEVICE_CLASSES_SCHEMA,
    STATE_CLASSES_SCHEMA as SENSOR_STATE_CLASSES_SCHEMA,
)
from homeassistant.components.switch import (
    DEVICE_CLASSES_SCHEMA as SWITCH_DEVICE_CLASSES_SCHEMA,
)
from homeassistant.config_entries import ConfigEntry, SOURCE_IMPORT
from homeassistant.const import (
    ATTR_STATE,
    CONF_ADDRESS,
    CONF_BINARY_SENSORS,
    CONF_COMMAND_OFF,
    CONF_COMMAND_ON,
    CONF_COUNT,
    CONF_COVERS,
    CONF_DELAY,
    CONF_DEVICE_CLASS,
    CONF_HOST,
    CONF_LIGHTS,
    CONF_METHOD,
    CONF_NAME,
    CONF_OFFSET,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_SENSORS,
    CONF_SLAVE,
    CONF_STRUCTURE,
    CONF_SWITCHES,
    CONF_TEMPERATURE_UNIT,
    CONF_TIMEOUT,
    CONF_TYPE,
    CONF_UNIQUE_ID,
    CONF_UNIT_OF_MEASUREMENT,
    EVENT_HOMEASSISTANT_STOP,
    SERVICE_RELOAD,
)
from homeassistant.core import Event, HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.reload import async_integration_yaml_config
from homeassistant.helpers.service import async_register_admin_service
from homeassistant.helpers.typing import ConfigType

from .const import (
    CALL_TYPE_COIL,
    CALL_TYPE_DISCRETE,
    CALL_TYPE_REGISTER_HOLDING,
    CALL_TYPE_REGISTER_INPUT,
    CALL_TYPE_WRITE_COIL,
    CALL_TYPE_WRITE_COILS,
    CALL_TYPE_WRITE_REGISTER,
    CALL_TYPE_WRITE_REGISTERS,
    CALL_TYPE_X_COILS,
    CALL_TYPE_X_REGISTER_HOLDINGS,
    CONF_BAUDRATE,
    CONF_BRIGHTNESS_REGISTER,
    CONF_BYTESIZE,
    CONF_CLIMATES,
    CONF_COLOR_TEMP_REGISTER,
    CONF_CURRENT_TEMP_OFFSET,
    CONF_CURRENT_TEMP_SCALE,
    CONF_DATA_TYPE,
    CONF_DEVICE_ADDRESS,
    CONF_DEVICE_INFO,
    CONF_DEVICES,
    CONF_HW_VERSION,
    CONF_MANUFACTURER,
    CONF_MODEL,
    CONF_SW_VERSION,
    CONF_FAN_MODE_AUTO,
    CONF_FAN_MODE_DIFFUSE,
    CONF_FAN_MODE_FOCUS,
    CONF_FAN_MODE_HIGH,
    CONF_FAN_MODE_LOW,
    CONF_FAN_MODE_MEDIUM,
    CONF_FAN_MODE_MIDDLE,
    CONF_FAN_MODE_OFF,
    CONF_FAN_MODE_ON,
    CONF_FAN_MODE_REGISTER,
    CONF_FAN_MODE_TOP,
    CONF_FAN_MODE_VALUES,
    CONF_FANS,
    CONF_NUMBERS,
    CONF_HVAC_ACTION_COOLING,
    CONF_HVAC_ACTION_DEFROSTING,
    CONF_HVAC_ACTION_DRYING,
    CONF_HVAC_ACTION_FAN,
    CONF_HVAC_ACTION_HEATING,
    CONF_HVAC_ACTION_IDLE,
    CONF_HVAC_ACTION_OFF,
    CONF_HVAC_ACTION_PREHEATING,
    CONF_HVAC_ACTION_REGISTER,
    CONF_HVAC_ACTION_VALUES,
    CONF_HVAC_MODE_AUTO,
    CONF_HVAC_MODE_COOL,
    CONF_HVAC_MODE_DRY,
    CONF_HVAC_MODE_FAN_ONLY,
    CONF_HVAC_MODE_HEAT,
    CONF_HVAC_MODE_HEAT_COOL,
    CONF_HVAC_MODE_OFF,
    CONF_HVAC_MODE_REGISTER,
    CONF_HVAC_MODE_VALUES,
    CONF_HVAC_OFF_VALUE,
    CONF_HVAC_ON_VALUE,
    CONF_HVAC_ONOFF_COIL,
    CONF_HVAC_ONOFF_REGISTER,
    CONF_INPUT_TYPE,
    CONF_MAX_TEMP,
    CONF_MAX_VALUE,
    CONF_MIN_TEMP,
    CONF_MIN_VALUE,
    CONF_MSG_WAIT,
    CONF_NAN_VALUE,
    CONF_PARITY,
    CONF_PRECISION,
    CONF_SCALE,
    CONF_SLAVE_COUNT,
    CONF_STATE_CLOSED,
    CONF_STATE_CLOSING,
    CONF_STATE_OFF,
    CONF_STATE_ON,
    CONF_STATE_OPEN,
    CONF_STATE_OPENING,
    CONF_STATUS_REGISTER,
    CONF_STATUS_REGISTER_TYPE,
    CONF_STEP,
    CONF_STOPBITS,
    CONF_SWAP,
    CONF_SWAP_BYTE,
    CONF_SWAP_WORD,
    CONF_SWAP_WORD_BYTE,
    CONF_SWING_MODE_REGISTER,
    CONF_SWING_MODE_SWING_BOTH,
    CONF_SWING_MODE_SWING_HORIZ,
    CONF_SWING_MODE_SWING_OFF,
    CONF_SWING_MODE_SWING_ON,
    CONF_SWING_MODE_SWING_VERT,
    CONF_SWING_MODE_VALUES,
    CONF_TARGET_TEMP,
    CONF_TARGET_TEMP_OFFSET,
    CONF_TARGET_TEMP_SCALE,
    CONF_TARGET_TEMP_WRITE_REGISTERS,
    CONF_VERIFY,
    CONF_VIRTUAL_COUNT,
    CONF_WRITE_REGISTERS,
    CONF_WRITE_TYPE,
    CONF_ZERO_SUPPRESS,
    DEFAULT_HUB,
    DEFAULT_HVAC_OFF_VALUE,
    DEFAULT_HVAC_ON_VALUE,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TEMP_UNIT,
    DOMAIN,
    PLATFORMS,
    RTUOVERTCP,
    SERIAL,
    TCP,
    UDP,
    DataType,
    ATTR_ADDRESS,
    ATTR_HUB,
    ATTR_SLAVE,
    ATTR_UNIT,
    ATTR_VALUE,
    SERVICE_STOP,
    SERVICE_WRITE_COIL,
    SERVICE_WRITE_REGISTER,
    SIGNAL_STOP_ENTITY,
)
from .modbus import DATA_MODBUS_HUBS, ModbusHub
from .validators import (
    check_config,
    duplicate_fan_mode_validator,
    duplicate_swing_mode_validator,
    ensure_and_check_conflicting_scales_and_offsets,
    hvac_fixedsize_reglist_validator,
    nan_validator,
    not_zero_value,
    register_int_list_validator,
    struct_validator,
)

_LOGGER = logging.getLogger(__name__)


BASE_SCHEMA = vol.Schema({vol.Optional(CONF_NAME, default=DEFAULT_HUB): cv.string})


BASE_COMPONENT_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_ADDRESS): cv.positive_int,
        vol.Exclusive(CONF_DEVICE_ADDRESS, "slave_addr"): cv.positive_int,
        vol.Exclusive(CONF_SLAVE, "slave_addr"): cv.positive_int,
        vol.Optional(
            CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
        ): cv.positive_int,
        vol.Optional(CONF_UNIQUE_ID): cv.string,
    }
)


BASE_STRUCT_SCHEMA = BASE_COMPONENT_SCHEMA.extend(
    {
        vol.Optional(CONF_INPUT_TYPE, default=CALL_TYPE_REGISTER_HOLDING): vol.In(
            [
                CALL_TYPE_REGISTER_HOLDING,
                CALL_TYPE_REGISTER_INPUT,
            ]
        ),
        vol.Optional(CONF_COUNT): cv.positive_int,
        vol.Optional(CONF_DATA_TYPE, default=DataType.INT16): vol.In(
            [
                DataType.INT16,
                DataType.INT32,
                DataType.INT64,
                DataType.UINT16,
                DataType.UINT32,
                DataType.UINT64,
                DataType.FLOAT16,
                DataType.FLOAT32,
                DataType.FLOAT64,
                DataType.STRING,
                DataType.CUSTOM,
            ]
        ),
        vol.Optional(CONF_STRUCTURE): cv.string,
        vol.Optional(CONF_SCALE): vol.All(
            vol.Coerce(float), lambda v: not_zero_value(v, "Scale cannot be zero.")
        ),
        vol.Optional(CONF_OFFSET): vol.Coerce(float),
        vol.Optional(CONF_PRECISION): cv.positive_int,
        vol.Optional(
            CONF_SWAP,
        ): vol.In(
            [
                CONF_SWAP_BYTE,
                CONF_SWAP_WORD,
                CONF_SWAP_WORD_BYTE,
            ]
        ),
    }
)


BASE_SWITCH_SCHEMA = BASE_COMPONENT_SCHEMA.extend(
    {
        vol.Optional(CONF_WRITE_TYPE, default=CALL_TYPE_REGISTER_HOLDING): vol.In(
            [
                CALL_TYPE_REGISTER_HOLDING,
                CALL_TYPE_COIL,
                CALL_TYPE_X_COILS,
                CALL_TYPE_X_REGISTER_HOLDINGS,
            ]
        ),
        vol.Optional(CONF_COMMAND_OFF, default=0x00): cv.positive_int,
        vol.Optional(CONF_COMMAND_ON, default=0x01): cv.positive_int,
        vol.Optional(CONF_VERIFY): vol.Maybe(
            {
                vol.Optional(CONF_ADDRESS): cv.positive_int,
                vol.Optional(CONF_INPUT_TYPE): vol.In(
                    [
                        CALL_TYPE_REGISTER_HOLDING,
                        CALL_TYPE_DISCRETE,
                        CALL_TYPE_REGISTER_INPUT,
                        CALL_TYPE_COIL,
                        CALL_TYPE_X_COILS,
                        CALL_TYPE_X_REGISTER_HOLDINGS,
                    ]
                ),
                vol.Optional(CONF_STATE_OFF): vol.All(
                    cv.ensure_list, [cv.positive_int]
                ),
                vol.Optional(CONF_STATE_ON): vol.All(cv.ensure_list, [cv.positive_int]),
                vol.Optional(CONF_DELAY, default=0): cv.positive_int,
            }
        ),
    }
)


CLIMATE_SCHEMA = vol.All(
    BASE_STRUCT_SCHEMA.extend(
        {
            vol.Required(CONF_TARGET_TEMP): hvac_fixedsize_reglist_validator,
            vol.Optional(CONF_TARGET_TEMP_WRITE_REGISTERS, default=False): cv.boolean,
            vol.Optional(CONF_MAX_TEMP, default=35): vol.Coerce(int),
            vol.Optional(CONF_MIN_TEMP, default=5): vol.Coerce(int),
            vol.Optional(CONF_STEP, default=0.5): vol.Coerce(float),
            vol.Optional(CONF_TEMPERATURE_UNIT, default=DEFAULT_TEMP_UNIT): cv.string,
            vol.Exclusive(CONF_HVAC_ONOFF_COIL, "hvac_onoff_type"): cv.positive_int,
            vol.Exclusive(CONF_HVAC_ONOFF_REGISTER, "hvac_onoff_type"): cv.positive_int,
            vol.Optional(CONF_CURRENT_TEMP_SCALE): vol.All(
                vol.Coerce(float),
                lambda v: not_zero_value(
                    v, "Current temperature scale cannot be zero."
                ),
            ),
            vol.Optional(CONF_TARGET_TEMP_SCALE): vol.All(
                vol.Coerce(float),
                lambda v: not_zero_value(v, "Target temperature scale cannot be zero."),
            ),
            vol.Optional(CONF_CURRENT_TEMP_OFFSET): vol.Coerce(float),
            vol.Optional(CONF_TARGET_TEMP_OFFSET): vol.Coerce(float),
            vol.Optional(
                CONF_HVAC_ON_VALUE, default=DEFAULT_HVAC_ON_VALUE
            ): cv.positive_int,
            vol.Optional(
                CONF_HVAC_OFF_VALUE, default=DEFAULT_HVAC_OFF_VALUE
            ): cv.positive_int,
            vol.Optional(CONF_WRITE_REGISTERS, default=False): cv.boolean,
            vol.Optional(CONF_HVAC_MODE_REGISTER): vol.Maybe(
                {
                    CONF_ADDRESS: cv.positive_int,
                    CONF_HVAC_MODE_VALUES: {
                        vol.Optional(CONF_HVAC_MODE_OFF): vol.Any(
                            cv.positive_int, [cv.positive_int]
                        ),
                        vol.Optional(CONF_HVAC_MODE_HEAT): vol.Any(
                            cv.positive_int, [cv.positive_int]
                        ),
                        vol.Optional(CONF_HVAC_MODE_COOL): vol.Any(
                            cv.positive_int, [cv.positive_int]
                        ),
                        vol.Optional(CONF_HVAC_MODE_HEAT_COOL): vol.Any(
                            cv.positive_int, [cv.positive_int]
                        ),
                        vol.Optional(CONF_HVAC_MODE_AUTO): vol.Any(
                            cv.positive_int, [cv.positive_int]
                        ),
                        vol.Optional(CONF_HVAC_MODE_DRY): vol.Any(
                            cv.positive_int, [cv.positive_int]
                        ),
                        vol.Optional(CONF_HVAC_MODE_FAN_ONLY): vol.Any(
                            cv.positive_int, [cv.positive_int]
                        ),
                    },
                    vol.Optional(CONF_WRITE_REGISTERS, default=False): cv.boolean,
                }
            ),
            vol.Optional(CONF_HVAC_ACTION_REGISTER): vol.Maybe(
                {
                    CONF_ADDRESS: cv.positive_int,
                    CONF_HVAC_ACTION_VALUES: {
                        vol.Optional(CONF_HVAC_ACTION_COOLING): vol.Any(
                            cv.positive_int, [cv.positive_int]
                        ),
                        vol.Optional(CONF_HVAC_ACTION_DEFROSTING): vol.Any(
                            cv.positive_int, [cv.positive_int]
                        ),
                        vol.Optional(CONF_HVAC_ACTION_DRYING): vol.Any(
                            cv.positive_int, [cv.positive_int]
                        ),
                        vol.Optional(CONF_HVAC_ACTION_FAN): vol.Any(
                            cv.positive_int, [cv.positive_int]
                        ),
                        vol.Optional(CONF_HVAC_ACTION_HEATING): vol.Any(
                            cv.positive_int, [cv.positive_int]
                        ),
                        vol.Optional(CONF_HVAC_ACTION_IDLE): vol.Any(
                            cv.positive_int, [cv.positive_int]
                        ),
                        vol.Optional(CONF_HVAC_ACTION_OFF): vol.Any(
                            cv.positive_int, [cv.positive_int]
                        ),
                        vol.Optional(CONF_HVAC_ACTION_PREHEATING): vol.Any(
                            cv.positive_int, [cv.positive_int]
                        ),
                    },
                    vol.Optional(
                        CONF_INPUT_TYPE, default=CALL_TYPE_REGISTER_HOLDING
                    ): vol.In(
                        [
                            CALL_TYPE_REGISTER_HOLDING,
                            CALL_TYPE_REGISTER_INPUT,
                        ]
                    ),
                }
            ),
            vol.Optional(CONF_FAN_MODE_REGISTER): vol.Maybe(
                vol.All(
                    {
                        vol.Required(CONF_ADDRESS): register_int_list_validator,
                        CONF_FAN_MODE_VALUES: {
                            vol.Optional(CONF_FAN_MODE_ON): cv.positive_int,
                            vol.Optional(CONF_FAN_MODE_OFF): cv.positive_int,
                            vol.Optional(CONF_FAN_MODE_AUTO): cv.positive_int,
                            vol.Optional(CONF_FAN_MODE_LOW): cv.positive_int,
                            vol.Optional(CONF_FAN_MODE_MEDIUM): cv.positive_int,
                            vol.Optional(CONF_FAN_MODE_HIGH): cv.positive_int,
                            vol.Optional(CONF_FAN_MODE_TOP): cv.positive_int,
                            vol.Optional(CONF_FAN_MODE_MIDDLE): cv.positive_int,
                            vol.Optional(CONF_FAN_MODE_FOCUS): cv.positive_int,
                            vol.Optional(CONF_FAN_MODE_DIFFUSE): cv.positive_int,
                        },
                    },
                    duplicate_fan_mode_validator,
                ),
            ),
            vol.Optional(CONF_SWING_MODE_REGISTER): vol.Maybe(
                vol.All(
                    {
                        vol.Required(CONF_ADDRESS): register_int_list_validator,
                        CONF_SWING_MODE_VALUES: {
                            vol.Optional(CONF_SWING_MODE_SWING_ON): cv.positive_int,
                            vol.Optional(CONF_SWING_MODE_SWING_OFF): cv.positive_int,
                            vol.Optional(CONF_SWING_MODE_SWING_HORIZ): cv.positive_int,
                            vol.Optional(CONF_SWING_MODE_SWING_VERT): cv.positive_int,
                            vol.Optional(CONF_SWING_MODE_SWING_BOTH): cv.positive_int,
                        },
                    },
                    duplicate_swing_mode_validator,
                )
            ),
        },
    ),
    ensure_and_check_conflicting_scales_and_offsets,
)

COVERS_SCHEMA = BASE_COMPONENT_SCHEMA.extend(
    {
        vol.Optional(
            CONF_INPUT_TYPE,
            default=CALL_TYPE_REGISTER_HOLDING,
        ): vol.In(
            [
                CALL_TYPE_REGISTER_HOLDING,
                CALL_TYPE_COIL,
            ]
        ),
        vol.Optional(CONF_DEVICE_CLASS): COVER_DEVICE_CLASSES_SCHEMA,
        vol.Optional(CONF_STATE_CLOSED, default=0): cv.positive_int,
        vol.Optional(CONF_STATE_CLOSING, default=3): cv.positive_int,
        vol.Optional(CONF_STATE_OPEN, default=1): cv.positive_int,
        vol.Optional(CONF_STATE_OPENING, default=2): cv.positive_int,
        vol.Optional(CONF_STATUS_REGISTER): cv.positive_int,
        vol.Optional(
            CONF_STATUS_REGISTER_TYPE,
            default=CALL_TYPE_REGISTER_HOLDING,
        ): vol.In([CALL_TYPE_REGISTER_HOLDING, CALL_TYPE_REGISTER_INPUT]),
    }
)

SWITCH_SCHEMA = BASE_SWITCH_SCHEMA.extend(
    {
        vol.Optional(CONF_DEVICE_CLASS): SWITCH_DEVICE_CLASSES_SCHEMA,
        vol.Exclusive(CONF_VIRTUAL_COUNT, "vir_switch_count"): cv.positive_int,
        vol.Exclusive(CONF_SLAVE_COUNT, "vir_switch_count"): cv.positive_int,
    }
)

LIGHT_SCHEMA = BASE_SWITCH_SCHEMA.extend(
    {
        vol.Optional(CONF_BRIGHTNESS_REGISTER): cv.positive_int,
        vol.Optional(CONF_COLOR_TEMP_REGISTER): cv.positive_int,
        vol.Optional(CONF_MIN_TEMP): cv.positive_int,
        vol.Optional(CONF_MAX_TEMP): cv.positive_int,
    }
)

FAN_SCHEMA = BASE_SWITCH_SCHEMA.extend({})

NUMBER_SCHEMA = vol.All(
    BASE_STRUCT_SCHEMA.extend(
        {
            vol.Optional(CONF_DEVICE_CLASS): SENSOR_DEVICE_CLASSES_SCHEMA,
            vol.Optional(CONF_UNIT_OF_MEASUREMENT): cv.string,
            vol.Optional(CONF_MIN_VALUE, default=0): vol.Coerce(float),
            vol.Optional(CONF_MAX_VALUE, default=100): vol.Coerce(float),
            vol.Optional("step"): vol.Coerce(float),
        }
    ),
    struct_validator,
)

SENSOR_SCHEMA = vol.All(
    BASE_STRUCT_SCHEMA.extend(
        {
            vol.Optional(CONF_DEVICE_CLASS): SENSOR_DEVICE_CLASSES_SCHEMA,
            vol.Optional(CONF_STATE_CLASS): SENSOR_STATE_CLASSES_SCHEMA,
            vol.Optional(CONF_UNIT_OF_MEASUREMENT): cv.string,
            vol.Exclusive(CONF_VIRTUAL_COUNT, "vir_sen_count"): cv.positive_int,
            vol.Exclusive(CONF_SLAVE_COUNT, "vir_sen_count"): cv.positive_int,
            vol.Optional(CONF_MIN_VALUE): vol.Coerce(float),
            vol.Optional(CONF_MAX_VALUE): vol.Coerce(float),
            vol.Optional(CONF_NAN_VALUE): nan_validator,
            vol.Optional(CONF_ZERO_SUPPRESS): cv.positive_float,
        }
    ),
)

BINARY_SENSOR_SCHEMA = BASE_COMPONENT_SCHEMA.extend(
    {
        vol.Optional(CONF_DEVICE_CLASS): BINARY_SENSOR_DEVICE_CLASSES_SCHEMA,
        vol.Optional(CONF_INPUT_TYPE, default=CALL_TYPE_COIL): vol.In(
            [
                CALL_TYPE_COIL,
                CALL_TYPE_DISCRETE,
                CALL_TYPE_REGISTER_HOLDING,
                CALL_TYPE_REGISTER_INPUT,
            ]
        ),
        vol.Exclusive(CONF_VIRTUAL_COUNT, "vir_bin_count"): cv.positive_int,
        vol.Exclusive(CONF_SLAVE_COUNT, "vir_bin_count"): cv.positive_int,
    }
)

def _make_device_schema() -> vol.Schema:
    """Build the device schema after all entity schemas are defined."""
    return vol.Schema(
        {
            vol.Required(CONF_NAME): cv.string,
            vol.Exclusive(CONF_DEVICE_ADDRESS, "slave_addr"): cv.positive_int,
            vol.Exclusive(CONF_SLAVE, "slave_addr"): cv.positive_int,
            vol.Optional(CONF_MANUFACTURER): cv.string,
            vol.Optional(CONF_MODEL): cv.string,
            vol.Optional(CONF_SW_VERSION): cv.string,
            vol.Optional(CONF_HW_VERSION): cv.string,
            vol.Optional(CONF_BINARY_SENSORS): vol.All(
                cv.ensure_list, [BINARY_SENSOR_SCHEMA]
            ),
            vol.Optional(CONF_CLIMATES): vol.All(
                cv.ensure_list, [vol.All(CLIMATE_SCHEMA, struct_validator)]
            ),
            vol.Optional(CONF_COVERS): vol.All(cv.ensure_list, [COVERS_SCHEMA]),
            vol.Optional(CONF_LIGHTS): vol.All(cv.ensure_list, [LIGHT_SCHEMA]),
            vol.Optional(CONF_SENSORS): vol.All(
                cv.ensure_list, [vol.All(SENSOR_SCHEMA, struct_validator)]
            ),
            vol.Optional(CONF_SWITCHES): vol.All(cv.ensure_list, [SWITCH_SCHEMA]),
            vol.Optional(CONF_FANS): vol.All(cv.ensure_list, [FAN_SCHEMA]),
            vol.Optional(CONF_NUMBERS): vol.All(cv.ensure_list, [NUMBER_SCHEMA]),
        }
    )


MODBUS_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_HUB): cv.string,
        vol.Optional(CONF_TIMEOUT, default=3): cv.socket_timeout,
        vol.Optional(CONF_DELAY, default=0): cv.positive_int,
        vol.Optional(CONF_MSG_WAIT): cv.positive_int,
        vol.Optional(CONF_BINARY_SENSORS): vol.All(
            cv.ensure_list, [BINARY_SENSOR_SCHEMA]
        ),
        vol.Optional(CONF_CLIMATES): vol.All(
            cv.ensure_list, [vol.All(CLIMATE_SCHEMA, struct_validator)]
        ),
        vol.Optional(CONF_COVERS): vol.All(cv.ensure_list, [COVERS_SCHEMA]),
        vol.Optional(CONF_LIGHTS): vol.All(cv.ensure_list, [LIGHT_SCHEMA]),
        vol.Optional(CONF_SENSORS): vol.All(
            cv.ensure_list, [vol.All(SENSOR_SCHEMA, struct_validator)]
        ),
        vol.Optional(CONF_SWITCHES): vol.All(cv.ensure_list, [SWITCH_SCHEMA]),
        vol.Optional(CONF_FANS): vol.All(cv.ensure_list, [FAN_SCHEMA]),
        vol.Optional(CONF_NUMBERS): vol.All(cv.ensure_list, [NUMBER_SCHEMA]),
        vol.Optional(CONF_DEVICES): vol.All(
            cv.ensure_list, [_make_device_schema()]
        ),
    },
    extra=vol.ALLOW_EXTRA,
)

SERIAL_SCHEMA = MODBUS_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): SERIAL,
        vol.Required(CONF_BAUDRATE): cv.positive_int,
        vol.Required(CONF_BYTESIZE): vol.Any(5, 6, 7, 8),
        vol.Required(CONF_METHOD): vol.Any("rtu", "ascii"),
        vol.Required(CONF_PORT): cv.string,
        vol.Required(CONF_PARITY): vol.Any("E", "O", "N"),
        vol.Required(CONF_STOPBITS): vol.Any(1, 2),
    }
)

ETHERNET_SCHEMA = MODBUS_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_PORT): cv.port,
        vol.Required(CONF_TYPE): vol.Any(TCP, UDP, RTUOVERTCP),
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.All(
            cv.ensure_list,
            [
                vol.Any(SERIAL_SCHEMA, ETHERNET_SCHEMA),
            ],
        ),
    },
    extra=vol.ALLOW_EXTRA,
)


def get_hub(hass: HomeAssistant, name: str) -> ModbusHub:
    """Return modbus hub with name."""
    return hass.data[DATA_MODBUS_HUBS][name]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Modbus from a config entry (created via YAML import)."""
    conf_hub = dict(entry.data)

    # Validate and normalise config
    checked = check_config(hass, [conf_hub])
    if not checked:
        return False
    conf_hub = checked[0]

    # Store processed config so platform setup functions can access it
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = conf_hub

    # Create and start hub
    hub_collect: dict[str, ModbusHub] = hass.data.setdefault(DATA_MODBUS_HUBS, {})
    my_hub = ModbusHub(hass, conf_hub)
    hub_collect[conf_hub[CONF_NAME]] = my_hub

    if not await my_hub.async_setup():
        hass.data[DOMAIN].pop(entry.entry_id, None)
        hub_collect.pop(conf_hub[CONF_NAME], None)
        return False

    # Close hub when HA stops
    async def _async_close_hub(_event: Event) -> None:
        await my_hub.async_close()

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _async_close_hub)
    )

    # Forward setup to all platforms (each checks if it has entities)
    await hass.config_entries.async_forward_entry_setups(
        entry, [platform for platform, _ in PLATFORMS]
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Modbus config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, [platform for platform, _ in PLATFORMS]
    )
    if unload_ok:
        hub_name = entry.data.get(CONF_NAME)
        hub: ModbusHub | None = hass.data.get(DATA_MODBUS_HUBS, {}).pop(hub_name, None)
        if hub:
            await hub.async_close()
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok


def _flatten_devices(conf_hub: dict) -> dict:
    """Expand device definitions into flat entity lists with injected device_info."""
    devices = conf_hub.pop(CONF_DEVICES, [])
    for device in devices:
        device_addr = device.get(CONF_DEVICE_ADDRESS) or device.get(CONF_SLAVE)
        device_info_data = {
            "name": device[CONF_NAME],
            CONF_MANUFACTURER: device.get(CONF_MANUFACTURER),
            CONF_MODEL: device.get(CONF_MODEL),
            CONF_SW_VERSION: device.get(CONF_SW_VERSION),
            CONF_HW_VERSION: device.get(CONF_HW_VERSION),
            "device_address": device_addr,
        }
        for _, conf_key in PLATFORMS:
            ents = device.get(conf_key, [])
            for entity_conf in ents:
                entity_conf = dict(entity_conf)
                entity_conf[CONF_DEVICE_INFO] = device_info_data
                if (
                    CONF_DEVICE_ADDRESS not in entity_conf
                    and CONF_SLAVE not in entity_conf
                    and device_addr is not None
                ):
                    entity_conf[CONF_DEVICE_ADDRESS] = device_addr
                conf_hub.setdefault(conf_key, []).append(entity_conf)
    return conf_hub


def _expand_slave_count(entities: list[dict]) -> list[dict]:
    """Expand slave_count/virtual_count entries into individual flat entity configs.

    Unlike sensors/binary_sensors (which share one combined read via a
    coordinator), switches read and write independently, so slave_count here
    is pure config-brevity: each extra instance is a normal, independent
    entity whose address is offset by its index. device_info (if present,
    e.g. injected by _flatten_devices) is inherited by every generated
    instance since it's carried over in the shallow copy.
    """
    expanded: list[dict] = []
    for entity_conf in entities:
        slave_count = entity_conf.get(CONF_SLAVE_COUNT) or entity_conf.get(
            CONF_VIRTUAL_COUNT, 0
        )
        if not slave_count:
            expanded.append(entity_conf)
            continue
        base_address = entity_conf[CONF_ADDRESS]
        base_name = entity_conf[CONF_NAME]
        base_unique_id = entity_conf.get(CONF_UNIQUE_ID)
        base_verify_address = None
        if entity_conf.get(CONF_VERIFY):
            base_verify_address = entity_conf[CONF_VERIFY].get(CONF_ADDRESS)
        for i in range(slave_count + 1):
            child = dict(entity_conf)
            child.pop(CONF_SLAVE_COUNT, None)
            child.pop(CONF_VIRTUAL_COUNT, None)
            child[CONF_ADDRESS] = base_address + i
            if i:
                child[CONF_NAME] = f"{base_name} {i}"
                if base_unique_id:
                    child[CONF_UNIQUE_ID] = f"{base_unique_id}_{i}"
                if base_verify_address is not None:
                    verify = dict(child[CONF_VERIFY])
                    verify[CONF_ADDRESS] = base_verify_address + i
                    child[CONF_VERIFY] = verify
            expanded.append(child)
    return expanded


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Modbus component from YAML configuration."""
    if DOMAIN not in config:
        return True

    # Ensure shared data structures exist
    hass.data.setdefault(DATA_MODBUS_HUBS, {})
    hass.data.setdefault(DOMAIN, {})

    # Preprocess each hub: expand device definitions into flat entity lists
    for conf_hub in config[DOMAIN]:
        _flatten_devices(conf_hub)
        if CONF_SWITCHES in conf_hub:
            conf_hub[CONF_SWITCHES] = _expand_slave_count(conf_hub[CONF_SWITCHES])
        # Create a config entry per hub via SOURCE_IMPORT
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data=conf_hub,
            )
        )

    # ── Reload service ────────────────────────────────────────────────────────
    async def _reload_config(call: Event | ServiceCall) -> None:
        """Reload Modbus: re-read YAML, update config entries, restart hubs."""
        reload_config = await async_integration_yaml_config(hass, DOMAIN)
        if not reload_config or DOMAIN not in reload_config:
            _LOGGER.debug("Modbus not present in reloaded config")
            return

        for conf_hub in reload_config[DOMAIN]:
            _flatten_devices(conf_hub)
            if CONF_SWITCHES in conf_hub:
                conf_hub[CONF_SWITCHES] = _expand_slave_count(conf_hub[CONF_SWITCHES])
            await hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data=conf_hub,
            )

        for entry in hass.config_entries.async_entries(DOMAIN):
            await hass.config_entries.async_reload(entry.entry_id)

    async_register_admin_service(hass, DOMAIN, SERVICE_RELOAD, _reload_config)

    # ── Hub services (write_register, write_coil, stop) ───────────────────────
    hub_collect: dict[str, ModbusHub] = hass.data[DATA_MODBUS_HUBS]

    def _get_service_call_details(
        service: ServiceCall,
    ) -> tuple[ModbusHub, int, int]:
        device_address = service.data.get(ATTR_SLAVE, service.data.get(ATTR_UNIT, 1))
        address = service.data[ATTR_ADDRESS]
        hub = hub_collect[service.data[ATTR_HUB]]
        return (hub, device_address, address)

    async def async_write_register(service: ServiceCall) -> None:
        hub, device_address, address = _get_service_call_details(service)
        value = service.data[ATTR_VALUE]
        if isinstance(value, list):
            await hub.async_pb_call(
                device_address, address, value, CALL_TYPE_WRITE_REGISTERS
            )
        else:
            await hub.async_pb_call(
                device_address, address, value, CALL_TYPE_WRITE_REGISTER
            )

    async def async_write_coil(service: ServiceCall) -> None:
        hub, device_address, address = _get_service_call_details(service)
        state = service.data[ATTR_STATE]
        if isinstance(state, list):
            await hub.async_pb_call(
                device_address, address, state, CALL_TYPE_WRITE_COILS
            )
        else:
            await hub.async_pb_call(
                device_address, address, state, CALL_TYPE_WRITE_COIL
            )

    async def async_stop_hub(service: ServiceCall) -> None:
        from homeassistant.helpers.dispatcher import async_dispatcher_send
        async_dispatcher_send(hass, SIGNAL_STOP_ENTITY)
        hub = hub_collect[service.data[ATTR_HUB]]
        await hub.async_close()

    for svc_name, svc_func, svc_field, svc_validator in (
        (SERVICE_WRITE_REGISTER, async_write_register, ATTR_VALUE, cv.positive_int),
        (SERVICE_WRITE_COIL, async_write_coil, ATTR_STATE, cv.boolean),
    ):
        hass.services.async_register(
            DOMAIN,
            svc_name,
            svc_func,
            schema=vol.Schema(
                {
                    vol.Optional(ATTR_HUB, default=DEFAULT_HUB): cv.string,
                    vol.Exclusive(ATTR_SLAVE, "unit"): cv.positive_int,
                    vol.Exclusive(ATTR_UNIT, "unit"): cv.positive_int,
                    vol.Required(ATTR_ADDRESS): cv.positive_int,
                    vol.Required(svc_field): vol.Any(
                        cv.positive_int, vol.All(cv.ensure_list, [svc_validator])
                    ),
                }
            ),
        )

    hass.services.async_register(
        DOMAIN,
        SERVICE_STOP,
        async_stop_hub,
        schema=vol.Schema({vol.Required(ATTR_HUB): cv.string}),
    )

    return True
