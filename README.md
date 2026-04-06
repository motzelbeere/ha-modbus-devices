# Modbus Integration with Device Support

A custom component for Home Assistant that extends the built-in [Modbus integration](https://github.com/home-assistant/core/tree/dev/homeassistant/components/modbus) with **device registry support** and **`!include`-based configuration**.

> **Base version:** HA Core `dev` branch — `homeassistant/components/modbus`

---

## What's new compared to the built-in integration

### `devices:` block in YAML
Group sensors and switches under a named device. All entities in the block are automatically linked to the same device in the Home Assistant Device Registry — visible in the UI under **Settings → Devices**.

```yaml
modbus:
  - name: my_hub
    type: tcp
    host: 192.168.1.100
    port: 502

    devices:
      - name: "My Device"
        manufacturer: "ACME Corp"
        model: "Model X"
        sw_version: "1.0"
        device_address: 1

        sensors:
          - name: "Temperature"
            address: 100
            data_type: float32
            unit_of_measurement: "°C"
            device_class: temperature

        switches:
          - name: "Relay 1"
            address: 200
            write_type: coil
```

### `!include` support for compact `configuration.yaml`
Keep your main config clean by splitting device definitions into separate files:

```yaml
# configuration.yaml
modbus: !include_dir_merge_list modbus/
```

```yaml
# modbus/wallbox.yaml
- name: wallbox_hub
  type: tcp
  host: 192.168.1.50
  port: 502
  devices:
    - name: "Wallbox"
      manufacturer: "ACME"
      device_address: 255
      sensors:
        ...
```

### Device Registry entries
Each `devices:` block creates a proper entry in the HA Device Registry with:
- Name, Manufacturer, Model
- Software / Hardware version (optional)
- All entities grouped under the device

---

## Installation

### Manual
1. Copy the `custom_components/modbus` folder into your HA config directory:
   ```
   /config/custom_components/modbus/
   ```
2. Restart Home Assistant.

### HACS (custom repository)
1. In HACS → **Custom repositories** → add this repo URL, category **Integration**.
2. Install "Modbus (with Device Support)".
3. Restart Home Assistant.

---

## Configuration

All existing Modbus YAML options remain unchanged. The `devices:` block is **additive** — you can mix `devices:` with the existing flat `sensors:`, `switches:` etc. at hub level.

### Device block options

| Key | Required | Description |
|-----|----------|-------------|
| `name` | ✅ | Device name shown in HA UI |
| `device_address` | ✅ | Modbus slave/unit address for all entities in this block |
| `manufacturer` | ❌ | Manufacturer string |
| `model` | ❌ | Model string |
| `sw_version` | ❌ | Software version string |
| `hw_version` | ❌ | Hardware version string |

Inside a `devices:` block, all standard platform sections are supported:

- `sensors:`
- `switches:`
- `binary_sensors:`
- `covers:`
- `fans:`
- `lights:`
- `climates:`

---

## Example configurations

See [`example_configs/`](example_configs/) for ready-to-use device definitions:

| File | Device |
|------|--------|
| [`wallbox_daheimlader.yaml`](example_configs/wallbox_daheimlader.yaml) | Daheimlader Wallbox (TCP Modbus) |

---

## Compatibility

| HA Version | Status |
|------------|--------|
| 2024.1+ | ✅ Tested |
| 2026.4 | ✅ Tested |

---

## How it works

The standard Modbus integration sets up entities via `async_load_platform` (YAML path), which has no Config Entry — so `device_info` is silently ignored by HA's entity platform code.

This fork uses the **`SOURCE_IMPORT` pattern**:

```
configuration.yaml
    ↓  async_setup() reads YAML, flattens devices: blocks
Config Entry (created automatically, invisible to user)
    ↓  async_setup_entry() initialises hub + entities
Device Registry entry created per devices: block
```

The user experience is identical to the built-in integration — only YAML configuration, no UI flow required.

---

## Credits

Based on the [Home Assistant Core Modbus integration](https://github.com/home-assistant/core/tree/dev/homeassistant/components/modbus) by the Home Assistant contributors, licensed under the Apache 2.0 License.
