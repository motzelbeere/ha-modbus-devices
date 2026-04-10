# Modbus Integration with Device Support

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

A custom component for Home Assistant that extends the built-in [Modbus integration](https://github.com/home-assistant/core/tree/dev/homeassistant/components/modbus) with **device registry support** and a clean, file-based configuration structure.

> **Basis:** HA Core `dev` — `homeassistant/components/modbus`

---

## Motivation

The built-in Modbus integration treats all entities as a flat list — there is no concept of a physical device. If you have multiple Modbus devices on the same bus (e.g. a heat pump, a wallbox, and a circulation pump), all their sensors and switches appear mixed together in Home Assistant with no grouping.

This integration adds a `devices:` block to the YAML configuration. Each physical device gets its own entry in the **Home Assistant Device Registry**, with all its entities grouped under it — visible and navigable in the UI under **Settings → Devices & Services → Modbus**.

---

## Was ist neu / What's new

### `devices:` Block

Geräte werden als benannte Blöcke definiert. Alle Entities innerhalb eines Blocks werden automatisch dem Gerät im HA Device Registry zugeordnet.

Devices are defined as named blocks. All entities within a block are automatically linked to the device in the HA Device Registry.

```yaml
modbus:
  - name: my_hub
    type: tcp
    host: 192.168.1.100
    port: 502

    devices:
      - name: "Heat Pump"
        manufacturer: "Vaillant"
        model: "aroTHERM plus"
        sw_version: "3.02"
        device_address: 1
        sensors:
          - name: "Flow Temperature"
            address: 100
            data_type: float32
            unit_of_measurement: "°C"
            device_class: temperature
            state_class: measurement
        switches:
          - name: "Heating Circuit"
            address: 200
            write_type: coil

      - name: "Circulation Pump"
        manufacturer: "Grundfos"
        device_address: 2
        sensors:
          - name: "Power"
            address: 50
            data_type: uint16
            unit_of_measurement: "W"
            device_class: power
```

### Geräteeigenschaften / Device properties

| Key | Pflicht / Required | Beschreibung / Description |
|-----|--------------------|---------------------------|
| `name` | ✅ | Gerätename in der HA-Oberfläche / Device name in HA UI |
| `device_address` | ✅ | Modbus Slave-/Unit-Adresse für alle Entities dieses Geräts / Modbus slave address for all entities in this block |
| `manufacturer` | ❌ | Hersteller / Manufacturer |
| `model` | ❌ | Modellbezeichnung / Model name |
| `sw_version` | ❌ | Softwareversion / Software version |
| `hw_version` | ❌ | Hardwareversion / Hardware version |

Innerhalb eines `devices:` Blocks werden alle Standard-Plattformen unterstützt:

All standard platform sections are supported inside a `devices:` block:

`sensors:` · `switches:` · `binary_sensors:` · `covers:` · `fans:` · `lights:` · `climates:`

### Modulare Konfiguration mit `!include`

Die `configuration.yaml` bleibt kompakt. Jedes Gerät lebt in einer eigenen Datei.

Keep `configuration.yaml` compact. Each device lives in its own file.

```yaml
# configuration.yaml
modbus: !include_dir_merge_list modbus/
```

```
/config/
├── configuration.yaml
└── modbus/
    ├── heat_pump.yaml
    ├── wallbox.yaml
    ├── circulation_pump.yaml
    └── valves.yaml
```

Jede Datei beginnt direkt mit dem Hub-Eintrag (ohne übergeordneten `modbus:` Schlüssel):

Each file starts directly with the hub entry (no top-level `modbus:` key):

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

---

## Installation

### Manuell / Manual

1. Den Ordner `custom_components/modbus` in das HA-Konfigurationsverzeichnis kopieren:
   Copy the `custom_components/modbus` folder into your HA config directory:
   ```
   /config/custom_components/modbus/
   ```
2. Home Assistant neu starten / Restart Home Assistant.

### HACS (empfohlen / recommended)

1. **HACS → Custom repositories** → diese Repo-URL eintragen, Kategorie **Integration**
   Add this repo URL, category **Integration**
2. „Modbus (with Device Support)" installieren / Install
3. Home Assistant neu starten / Restart Home Assistant

---

## Kompatibilität / Compatibility

| HA Version | Status |
|------------|--------|
| 2024.1+ | ✅ |
| 2026.4 | ✅ Tested |

Alle bestehenden Modbus-YAML-Optionen bleiben unverändert. Der `devices:` Block ist additiv — vorhandene flache `sensors:`, `switches:` etc. auf Hub-Ebene funktionieren weiterhin.

All existing Modbus YAML options remain unchanged. The `devices:` block is additive — existing flat `sensors:`, `switches:` etc. at hub level continue to work.

---

## Funktionsweise / How it works

Die Standard-Modbus-Integration richtet Entities über `async_load_platform` ein — ohne Config Entry. HA's Entity-Platform-Code ignoriert `device_info` in diesem Fall stillschweigend.

Diese Integration verwendet das **`SOURCE_IMPORT`-Pattern**: Die YAML-Konfiguration erzeugt automatisch einen unsichtbaren Config Entry. Dadurch wird `device_info` korrekt verarbeitet und ein Device-Registry-Eintrag angelegt.

The standard Modbus integration sets up entities via `async_load_platform` — without a Config Entry. HA's entity platform code silently ignores `device_info` in this case.

This integration uses the **`SOURCE_IMPORT` pattern**: the YAML configuration automatically creates an invisible Config Entry, which allows `device_info` to be processed correctly and a Device Registry entry to be created.

```
configuration.yaml
    ↓  async_setup() liest YAML, verarbeitet devices: Blöcke
       async_setup() reads YAML, processes devices: blocks
Config Entry (automatisch / created automatically)
    ↓  async_setup_entry() initialisiert Hub + Entities
       async_setup_entry() initialises hub + entities
Device Registry Eintrag pro devices: Block
Device Registry entry per devices: block
```

---

## Beispielkonfigurationen / Example configurations

Fertige Gerätedefinitionen unter / Ready-to-use device definitions in [`example_configs/`](example_configs/).

---

## Lizenz / License

Basiert auf der [Home Assistant Core Modbus Integration](https://github.com/home-assistant/core/tree/dev/homeassistant/components/modbus) der Home Assistant Mitwirkenden.
Licensed under the [Apache License 2.0](LICENSE).

Based on the [Home Assistant Core Modbus integration](https://github.com/home-assistant/core/tree/dev/homeassistant/components/modbus) by the Home Assistant contributors.
