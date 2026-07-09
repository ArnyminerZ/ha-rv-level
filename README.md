# RV Level

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![Validate](https://github.com/arnyminerz/ha-rv-level/actions/workflows/validate.yaml/badge.svg)](https://github.com/arnyminerz/ha-rv-level/actions/workflows/validate.yaml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A Home Assistant custom integration that turns your van/RV's pitch and roll
readings into **how many centimeters to lift each wheel**, and **which
chock/leveler to use** for it, so you can get level at a campsite without
guesswork.

> [!IMPORTANT]
> **This entire repository — the integration's code, its config flow, the
> leveling algorithm, presets, tests, and this documentation — was generated
> with the help of an AI coding assistant (Claude, by Anthropic), based on a
> hand-written Jinja template the author had been using for their own van.**
> It has been reviewed and tested (see [`tests/`](tests/)) but, as with any
> AI-assisted project, please review the code yourself before trusting it
> with your rig, and double-check the vehicle/chock preset numbers against
> your own vehicle before relying on them (see
> [Accuracy of presets](#accuracy-of-presets) below).

## What it does

You already have (or can add cheaply) a Bluetooth or ESPHome inclinometer
reporting **pitch** and **roll** in degrees as two Home Assistant sensors.
This integration takes those two sensors plus your vehicle's dimensions and
turns them into, per wheel:

- how many centimeters that wheel needs to be raised to level the vehicle,
- which chock height (from the chocks/levelers you own) gets you closest to
  that,
- whether the vehicle is level *right now*, and
- whether it's *possible* to get level at all with the chocks you have.

The math models the vehicle as a rigid plane and is documented in detail in
[`custom_components/rv_level/solver.py`](custom_components/rv_level/solver.py).

## Installation

### HACS (recommended)

This integration is not (yet) in the default HACS store, so add it as a
custom repository:

1. HACS -> the "..." menu (top right) -> **Custom repositories**.
2. Repository: `https://github.com/arnyminerz/ha-rv-level`, category:
   **Integration**.
3. Install "RV Level", then restart Home Assistant.

### Manual

Copy `custom_components/rv_level` into your Home Assistant `config/custom_components/`
directory, then restart Home Assistant.

## Setup

Settings -> Devices & services -> Add integration -> **RV Level**. The
config flow walks you through:

1. **Pitch & roll sensors** — pick the two sensors your inclinometer already
   provides.
2. **Vehicle dimensions** — pick a base-vehicle preset (prefills the next
   step) or Custom, then confirm/edit the wheelbase and track width.
3. **Margins** — the pitch/roll tolerance (in degrees) within which the
   vehicle counts as "level". Defaults to 1.5° each.
4. **Chocks/levelers** — pick a chock preset or Custom, then confirm/edit how
   many chocks you have available at once (defaults to 2).

Everything above can be changed later without removing the integration: open
the RV Level integration entry and choose **Reconfigure**. This re-runs the
same wizard pre-filled with your current values — handy for e.g. loosening
the margins or swapping to a different set of chocks.

### Built-in vehicle presets

| Preset | Wheelbase | Track width |
|---|---|---|
| Fiat Ducato / Peugeot Boxer / Citroën Jumper (Standard, 3000 mm) | 300 cm | 198 cm |
| Fiat Ducato / Peugeot Boxer / Citroën Jumper (Medium, 3450 mm) | 345 cm | 198 cm |
| Fiat Ducato / Peugeot Boxer / Citroën Jumper (Maxi, 4035 mm) | 403.5 cm | 198 cm |
| Mercedes-Benz Sprinter (3665 mm) | 366.5 cm | 173.4 cm |
| Mercedes-Benz Sprinter (4325 mm, long) | 432.5 cm | 173.4 cm |
| Volkswagen Crafter / MAN TGE (3640 mm) | 364 cm | 185 cm |
| Ford Transit (3300 mm) | 330 cm | 175 cm |
| Custom | *you enter both* | |

### Built-in chock presets

| Preset | Step heights | Default count |
|---|---|---|
| Fiamma Kit Level Up | 4 / 7 / 10 cm | 2 |
| Fiamma Level Up (single wedge) | 2 / 4 / 6 / 8 cm | 2 |
| Thule Leveler | 4.5 / 9 cm | 2 |
| Custom | *you enter your own heights* | *you choose* |

The chock count is always editable regardless of preset — set it to however
many chocks you actually own.

#### Accuracy of presets

The Fiamma Kit Level Up figures come straight from the author's own set and
are used as-is. The rest are community-sourced best-effort approximations —
please verify against your own vehicle/product documentation, and see
[CONTRIBUTING.md](CONTRIBUTING.md) if you'd like to correct or add one.

## Entities created

Per config entry (i.e. per vehicle), a device is created with these entities
(entity IDs below assume the default device name "RV Level" — Home Assistant
slugs this into `rv_level`; check Settings -> Devices & services -> RV Level
for your actual IDs):

| Entity | Description |
|---|---|
| `sensor.rv_level_front_left_lift` (+ `_front_right`, `_rear_left`, `_rear_right`) | Raw centimeters that wheel needs to be raised |
| `sensor.rv_level_front_left_chock` (+ other corners) | Height of the chock to place under that wheel (0 = none), with a `chock_index` attribute |
| `sensor.rv_level_wheels_to_lift` | How many wheels currently need a chock |
| `sensor.rv_level_bubble_position` | Normalized bubble-level position/margins as attributes, for dashboard cards |
| `binary_sensor.rv_level_level` | On when the vehicle is level right now, no chocks needed |
| `binary_sensor.rv_level_levelable` | On when your configured chocks can bring it within margins |

## Recorder / history

All of these sensors are derived values, recomputed on every pitch/roll
update — there's little value in keeping their history, and it adds
unnecessary rows to your recorder database. Consider excluding them (and
your raw pitch/roll sensors) in `configuration.yaml`:

```yaml
recorder:
  exclude:
    entities:
    - sensor.van_pitch
    - sensor.van_roll
    # Values provided by the RV Level Integration
    - sensor.rv_level_bubble_position
    - sensor.rv_level_front_left_chock
    - sensor.rv_level_front_left_lift
    - sensor.rv_level_front_right_chock
    - sensor.rv_level_front_right_lift
    - sensor.rv_level_rear_left_chock
    - sensor.rv_level_rear_left_lift
    - sensor.rv_level_rear_right_chock
    - sensor.rv_level_rear_right_lift
    - sensor.rv_level_wheels_to_lift
```

Replace `sensor.van_pitch` / `sensor.van_roll` with your own inclinometer
entities, and adjust the `rv_level_*` IDs if your device isn't named the
default "RV Level".

## Custom Cards

I provide this repository: https://github.com/ArnyminerZ/ha-rv-level-cards
if you want some custom cards to display the values.

## Dashboard extras

A bubble-level card and a per-wheel chock display card are provided as a
*starting point* in [`lovelace/`](lovelace/) — these can't ship automatically
through an "integration" HACS repository, so copy/adapt them by hand. See
[`lovelace/README.md`](lovelace/README.md) for prerequisites and setup.

## Contributing

New vehicle or chock presets, and corrections to existing ones, are very
welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
