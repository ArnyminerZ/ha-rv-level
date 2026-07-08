"""Data update coordinator for RV Level.

Unlike a typical polling coordinator, this one has no update interval: the
leveling solution only needs to change when the pitch or roll sensor
changes, so a state-change listener triggers the refresh instead.
"""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_CHOCK_COUNT,
    CONF_CHOCK_STEPS,
    CONF_PITCH_ENTITY,
    CONF_PITCH_MARGIN,
    CONF_ROLL_ENTITY,
    CONF_ROLL_MARGIN,
    CONF_TRACK_WIDTH,
    CONF_WHEELBASE,
    DOMAIN,
)
from .solver import LevelResult, solve

_LOGGER = logging.getLogger(__name__)


class RVLevelCoordinator(DataUpdateCoordinator[LevelResult]):
    """Recomputes the leveling solution whenever pitch/roll change."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=None)
        self.entry = entry
        self._unsub_state_change: callback | None = None

    def _read_angle(self, entity_id: str) -> float:
        state = self.hass.states.get(entity_id)
        if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            raise UpdateFailed(f"{entity_id} is unavailable")
        try:
            return float(state.state)
        except ValueError as err:
            raise UpdateFailed(f"{entity_id} state is not numeric: {state.state}") from err

    async def _async_update_data(self) -> LevelResult:
        data = self.entry.data
        pitch = self._read_angle(data[CONF_PITCH_ENTITY])
        roll = self._read_angle(data[CONF_ROLL_ENTITY])

        return solve(
            pitch=pitch,
            roll=roll,
            wheelbase_cm=data[CONF_WHEELBASE],
            track_width_cm=data[CONF_TRACK_WIDTH],
            pitch_margin=data[CONF_PITCH_MARGIN],
            roll_margin=data[CONF_ROLL_MARGIN],
            chock_steps_cm=data[CONF_CHOCK_STEPS],
            chock_count=data[CONF_CHOCK_COUNT],
        )

    async def async_setup(self) -> None:
        """Do the first refresh and start listening for sensor updates."""
        await self.async_config_entry_first_refresh()
        self._unsub_state_change = async_track_state_change_event(
            self.hass,
            [self.entry.data[CONF_PITCH_ENTITY], self.entry.data[CONF_ROLL_ENTITY]],
            self._handle_source_event,
        )

    @callback
    def _handle_source_event(self, event: Event[EventStateChangedData]) -> None:
        self.hass.async_create_task(self.async_refresh())

    def async_unload(self) -> None:
        """Stop listening for sensor updates."""
        if self._unsub_state_change is not None:
            self._unsub_state_change()
            self._unsub_state_change = None
