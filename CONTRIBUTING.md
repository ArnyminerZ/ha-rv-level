# Contributing

Thanks for considering a contribution! This is a small, community-maintained
integration, so the most valuable contributions by far are **new or
corrected vehicle and chock presets** — you don't need to write any Python
logic for those, just edit a dataclass table.

## Adding or correcting a vehicle preset

Vehicle presets live in
[`custom_components/rv_level/presets.py`](custom_components/rv_level/presets.py),
in the `VEHICLE_PRESETS` dict:

```python
"ducato_maxi": VehiclePreset(
    name="Fiat Ducato / Peugeot Boxer / Citroën Jumper (Maxi, 4035 mm)",
    wheelbase_cm=403.5,
    track_width_cm=198.0,
),
```

To add a new one:

1. Pick a short, stable `snake_case` key (used internally, never shown to
   users — once released, avoid renaming it, since it would silently reset
   anyone using it back to their last-confirmed dimensions on next reconfigure).
2. `name` is what users see in the dropdown. Include enough detail to
   disambiguate wheelbase/body variants (many base vans are sold under
   several badges with the same chassis, and manufacturers offer multiple
   wheelbase lengths).
3. `wheelbase_cm`: the distance between the center of a front wheel and the
   center of the rear wheel on the same side, in **centimeters**.
4. `track_width_cm`: the distance between the centers of the two wheels on
   the same axle, in **centimeters**. Front and rear track width often
   differ slightly on the same vehicle — prefer the **front** axle figure,
   since that's what typically determines how the van rocks side to side
   once the front is on chocks.
5. Optionally set `note` for anything a user should know before trusting the
   preset (e.g. "rear track is narrower — treat this as approximate").

Please **cite your source** in the pull request description (manufacturer
spec sheet, forum measurement thread, your own tape-measure reading, etc.) —
we'd rather have fewer presets that are trustworthy than many that aren't.

### Correcting an existing preset

If you have a more accurate figure (e.g. from official manufacturer specs)
for a preset already in the table, please open a PR updating the numbers and
explain the discrepancy and your source. Several current entries are
best-effort approximations pending exactly this kind of correction.

## Adding or correcting a chock/leveler preset

Chock presets live in the same file, in the `CHOCK_PRESETS` dict:

```python
"thule_leveler": ChockPreset(
    name="Thule Leveler",
    steps_cm=(4.5, 9.0),
    default_count=2,
    note="Approximate — interlocking wedge set that can be stacked to roughly "
    "double height. Please verify against your exact set.",
),
```

- `steps_cm`: every distinct height the chock/leveler can achieve, in
  centimeters, ascending. For a set of ramps sold at fixed heights (like the
  Fiamma Kit Level Up), this is just each ramp's height. For a stackable
  wedge, include every achievable *combined* height, not just a single
  wedge's height.
- `default_count`: how many of this chock a user typically owns — this is
  only a prefill; users can always override the count in their own config.
- `note`: use this for anything users should double check (approximate
  figures, assumptions about how stacking works, etc.).

## Improving the leveling algorithm

The math lives in
[`custom_components/rv_level/solver.py`](custom_components/rv_level/solver.py)
and is deliberately documented in-depth at the top of the file and around the
trickier steps (nearest-chock selection under a limited chock count, and the
residual-tilt calculation used for the "levelable" check). If you think the
model is wrong or can be improved, please:

1. Read that module's docstring first — it explains the rigid-plane
   assumption the whole thing is built on.
2. Add/adjust a test in [`tests/test_solver.py`](tests/test_solver.py)
   demonstrating the scenario you're fixing or improving, in addition to
   your fix.

## Running tests

```bash
pip install pytest
pytest tests/
```

`tests/test_solver.py` only imports `solver.py`, which has no Home Assistant
dependency, so this runs fast with no extra setup.

## Config flow / entity changes

If you're changing `config_flow.py`, `coordinator.py`, or the entity
platforms, please also update `strings.json` **and**
`translations/en.json` together (they must stay in sync — Home Assistant
reads `strings.json` as the source of truth for the default English
translation, but custom integrations must ship `translations/en.json`
explicitly).

## Adding an entity name translation

Entity **display names** (not entity IDs, see below) are translated the
standard Home Assistant way: `custom_components/rv_level/translations/<lang>.json`,
keyed by [two-letter language code](https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes)
(`en`, `ca`, `es`, ...). To add a new language, create
`translations/<lang>.json` with just the `entity` section, translating every
`name` value:

```json
{
  "entity": {
    "sensor": {
      "front_left_lift": { "name": "Front left lift" },
      "front_right_lift": { "name": "Front right lift" },
      "rear_left_lift": { "name": "Rear left lift" },
      "rear_right_lift": { "name": "Rear right lift" },
      "front_left_chock": { "name": "Front left chock" },
      "front_right_chock": { "name": "Front right chock" },
      "rear_left_chock": { "name": "Rear left chock" },
      "rear_right_chock": { "name": "Rear right chock" },
      "wheels_to_lift": { "name": "Wheels to lift" },
      "bubble_position": { "name": "Bubble position" }
    },
    "binary_sensor": {
      "level": { "name": "Level" },
      "levelable": { "name": "Levelable" }
    }
  }
}
```

- Only translate the `name` **values** — the outer keys (`front_left_lift`,
  `level`, ...) are translation keys the code looks up by, and must stay
  exactly as above.
- No need to copy the `config` (config flow) section into a new
  `translations/<lang>.json` — Home Assistant falls back to English
  (`strings.json`) for anything a translation file doesn't include, so a
  partial translation (entity names only) is perfectly fine.
- No Python or JSON schema changes needed beyond the new file — it's picked
  up automatically.

### Why entity IDs never change with the language

You may notice the entity's *name* translates but its entity_id (e.g.
`sensor.rv_level_front_left_lift`) doesn't, even for languages — like
Catalan and Spanish — that Home Assistant would otherwise use to generate
entity IDs for brand-new entities. This integration deliberately overrides
`suggested_object_id` in [`entity.py`](custom_components/rv_level/entity.py)
to pin every entity's generated ID to a fixed English suffix, independent of
the display name/translation. This matters because dashboard cards, the
recorder-exclude example in the README, and any automations you write all
key off those fixed suffixes — if you add a new entity, please set
`self._object_id_suffix` in its `__init__` the same way the existing ones
do, so it gets the same guarantee.
