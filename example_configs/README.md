# Example Configurations

Ready-to-use device definitions for the Modbus integration with device support.

## Usage

Each file contains one or more hub definitions using the `devices:` block.
They are designed for use with `!include` or `!include_dir_merge_list` in `configuration.yaml`.

### Single file include
```yaml
# configuration.yaml
modbus: !include modbus/wallbox.yaml
```

### Multiple files (merge list)
```yaml
# configuration.yaml
modbus: !include_dir_merge_list modbus/
```
Place all device YAML files in a `modbus/` folder next to `configuration.yaml`.

---

## Available examples

| File | Device | Format | Entities |
|------|--------|--------|----------|
| `wallbox_daheimlader.yaml` | Daheimlader Wallbox | `devices:` block (new) | 58 sensors, 3 switches |
| `wallbox_daheimlader_legacy.yaml` | Daheimlader Wallbox | flat list (legacy) | 58 sensors, 3 switches |
| `multichannel_meter_slave_count.yaml` | Multi-Channel Meter | `devices:` block + `slave_count` | 2 definitions -> 8 sensors, 1 combined read each |

The legacy file shows the same device in the standard Modbus format — useful as a before/after comparison.

---

## Adding your own device

Copy any example file, adjust `host`, `port`, `device_address` and the entity list to match your device's Modbus register map.
