"""Config flow for RV Level.

The flow is a short wizard: pick the pitch/roll sensors, pick (or hand-enter)
the vehicle's dimensions, set the pitch/roll margins, and pick (or hand-enter)
the chocks/levelers you own. The exact same steps are reused for the
reconfigure flow (Settings -> Devices & services -> RV Level -> Reconfigure),
pre-filled with the entry's current values, so margins and everything else
can be changed later without deleting and re-adding the integration.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import SOURCE_RECONFIGURE, ConfigFlow, ConfigFlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_CHOCK_COUNT,
    CONF_CHOCK_PRESET,
    CONF_CHOCK_STEPS,
    CONF_PITCH_ENTITY,
    CONF_PITCH_MARGIN,
    CONF_ROLL_ENTITY,
    CONF_ROLL_MARGIN,
    CONF_TRACK_WIDTH,
    CONF_VEHICLE_PRESET,
    CONF_WHEELBASE,
    CUSTOM_PRESET,
    DEFAULT_CHOCK_COUNT,
    DEFAULT_PITCH_MARGIN_DEG,
    DEFAULT_ROLL_MARGIN_DEG,
    DEFAULT_TRACK_WIDTH_CM,
    DEFAULT_WHEELBASE_CM,
    DOMAIN,
)
from .presets import CHOCK_PRESETS, VEHICLE_PRESETS


def _select(options: dict[str, Any]) -> selector.SelectSelector:
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                selector.SelectOptionDict(value=key, label=preset.name)
                for key, preset in options.items()
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _length_number() -> selector.NumberSelector:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=50,
            max=1000,
            step=0.5,
            unit_of_measurement="cm",
            mode=selector.NumberSelectorMode.BOX,
        )
    )


def _margin_number() -> selector.NumberSelector:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=0.1,
            max=10,
            step=0.1,
            unit_of_measurement="°",
            mode=selector.NumberSelectorMode.BOX,
        )
    )


def _parse_chock_steps(raw: str) -> list[float]:
    steps = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        value = float(chunk)
        if value <= 0:
            raise ValueError("chock step must be positive")
        steps.append(value)
    if not steps:
        raise ValueError("no chock steps given")
    return sorted(steps)


class RVLevelConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config (and reconfigure) flow for RV Level."""

    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    def _existing_data(self) -> Mapping[str, Any]:
        if self.source == SOURCE_RECONFIGURE:
            return self._get_reconfigure_entry().data
        return {}

    # -- Step 1: pitch/roll entities -----------------------------------

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        existing = self._existing_data()

        if user_input is not None:
            unique_id = f"{user_input[CONF_PITCH_ENTITY]}::{user_input[CONF_ROLL_ENTITY]}"
            await self.async_set_unique_id(unique_id)
            if self.source != SOURCE_RECONFIGURE:
                self._abort_if_unique_id_configured()
            self._data.update(user_input)
            return await self.async_step_vehicle()

        schema = self.add_suggested_values_to_schema(
            vol.Schema(
                {
                    vol.Required(CONF_PITCH_ENTITY): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="sensor")
                    ),
                    vol.Required(CONF_ROLL_ENTITY): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="sensor")
                    ),
                }
            ),
            existing,
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    # -- Step 2: vehicle preset ------------------------------------------

    async def async_step_vehicle(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        existing = self._existing_data()

        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_dimensions()

        schema = self.add_suggested_values_to_schema(
            vol.Schema(
                {
                    vol.Required(
                        CONF_VEHICLE_PRESET, default=CUSTOM_PRESET
                    ): _select(VEHICLE_PRESETS),
                }
            ),
            existing,
        )
        return self.async_show_form(step_id="vehicle", data_schema=schema)

    # -- Step 3: dimensions, pre-filled from the chosen preset ------------

    async def async_step_dimensions(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        existing = self._existing_data()

        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_margins()

        preset = VEHICLE_PRESETS.get(self._data.get(CONF_VEHICLE_PRESET, CUSTOM_PRESET))
        suggested = {
            CONF_WHEELBASE: existing.get(
                CONF_WHEELBASE, preset.wheelbase_cm if preset else DEFAULT_WHEELBASE_CM
            ),
            CONF_TRACK_WIDTH: existing.get(
                CONF_TRACK_WIDTH, preset.track_width_cm if preset else DEFAULT_TRACK_WIDTH_CM
            ),
        }
        schema = self.add_suggested_values_to_schema(
            vol.Schema(
                {
                    vol.Required(CONF_WHEELBASE): _length_number(),
                    vol.Required(CONF_TRACK_WIDTH): _length_number(),
                }
            ),
            suggested,
        )
        description_placeholders = {"preset_note": preset.note if preset else ""}
        return self.async_show_form(
            step_id="dimensions",
            data_schema=schema,
            description_placeholders=description_placeholders,
        )

    # -- Step 4: margins --------------------------------------------------

    async def async_step_margins(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        existing = self._existing_data()

        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_chocks()

        schema = self.add_suggested_values_to_schema(
            vol.Schema(
                {
                    vol.Required(
                        CONF_PITCH_MARGIN, default=DEFAULT_PITCH_MARGIN_DEG
                    ): _margin_number(),
                    vol.Required(
                        CONF_ROLL_MARGIN, default=DEFAULT_ROLL_MARGIN_DEG
                    ): _margin_number(),
                }
            ),
            existing,
        )
        return self.async_show_form(step_id="margins", data_schema=schema)

    # -- Step 5: chock preset ----------------------------------------------

    async def async_step_chocks(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        existing = self._existing_data()

        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_chock_details()

        schema = self.add_suggested_values_to_schema(
            vol.Schema(
                {
                    vol.Required(
                        CONF_CHOCK_PRESET, default="fiamma_kit_level_up"
                    ): _select(CHOCK_PRESETS),
                }
            ),
            existing,
        )
        return self.async_show_form(step_id="chocks", data_schema=schema)

    # -- Step 6: chock count (+ heights, if custom) -> create/update entry -

    async def async_step_chock_details(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        existing = self._existing_data()
        preset_key = self._data.get(CONF_CHOCK_PRESET, CUSTOM_PRESET)
        preset = CHOCK_PRESETS.get(preset_key)
        is_custom = preset_key == CUSTOM_PRESET

        if user_input is not None:
            chock_count = int(user_input[CONF_CHOCK_COUNT])
            if is_custom:
                try:
                    steps = _parse_chock_steps(user_input[CONF_CHOCK_STEPS])
                except ValueError:
                    errors[CONF_CHOCK_STEPS] = "invalid_chock_steps"
                else:
                    self._data[CONF_CHOCK_STEPS] = steps
                    self._data[CONF_CHOCK_COUNT] = chock_count
            else:
                self._data[CONF_CHOCK_STEPS] = list(preset.steps_cm)
                self._data[CONF_CHOCK_COUNT] = chock_count

            if not errors:
                return self._finish()

        suggested = {
            CONF_CHOCK_COUNT: existing.get(
                CONF_CHOCK_COUNT, preset.default_count if preset else DEFAULT_CHOCK_COUNT
            ),
            CONF_CHOCK_STEPS: ", ".join(
                str(v) for v in existing.get(CONF_CHOCK_STEPS, preset.steps_cm if preset else ())
            ),
        }
        fields: dict[Any, Any] = {
            vol.Required(CONF_CHOCK_COUNT): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1, max=8, step=1, mode=selector.NumberSelectorMode.BOX
                )
            ),
        }
        if is_custom:
            fields[vol.Required(CONF_CHOCK_STEPS)] = selector.TextSelector()

        schema = self.add_suggested_values_to_schema(vol.Schema(fields), suggested)
        description_placeholders = {"preset_note": preset.note if preset else ""}
        return self.async_show_form(
            step_id="chock_details",
            data_schema=schema,
            errors=errors,
            description_placeholders=description_placeholders,
        )

    def _finish(self) -> ConfigFlowResult:
        if self.source == SOURCE_RECONFIGURE:
            entry = self._get_reconfigure_entry()
            return self.async_update_reload_and_abort(entry, data=self._data)

        # Kept short and constant on purpose: this becomes the device name,
        # which in turn seeds every entity_id (e.g. sensor.rv_level_front_left_lift).
        # It can be renamed afterwards from Settings -> Devices without changing
        # the already-generated entity_ids.
        return self.async_create_entry(title="RV Level", data=self._data)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self.async_step_user(user_input)
