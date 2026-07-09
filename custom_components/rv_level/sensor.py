"""Sensor entities for RV Level."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_PITCH_MARGIN, CONF_ROLL_MARGIN, CORNERS, DOMAIN
from .coordinator import RVLevelCoordinator
from .entity import RVLevelEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up RV Level sensors for a config entry."""
    coordinator: RVLevelCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []
    for corner in CORNERS:
        entities.append(RVLevelLiftSensor(coordinator, entry, corner))
        entities.append(RVLevelChockSensor(coordinator, entry, corner))
    entities.append(RVLevelWheelsToLiftSensor(coordinator, entry))
    entities.append(RVLevelPitchSensor(coordinator, entry))
    entities.append(RVLevelRollSensor(coordinator, entry))

    async_add_entities(entities)


class RVLevelLiftSensor(RVLevelEntity, SensorEntity):
    """How much a given wheel needs to be raised, in cm."""

    _attr_native_unit_of_measurement = "cm"
    _attr_icon = "mdi:arrow-up-bold-box"
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: RVLevelCoordinator, entry: ConfigEntry, corner: str) -> None:
        super().__init__(coordinator, entry)
        self._corner = corner
        self._attr_translation_key = f"{corner}_lift"
        self._attr_unique_id = f"{entry.entry_id}_{corner}_lift"
        self._object_id_suffix = f"{corner}_lift"

    @property
    def native_value(self) -> float:
        return self.coordinator.data.lift_cm[self._corner]


class RVLevelChockSensor(RVLevelEntity, SensorEntity):
    """Height of the chock to place under a given wheel, in cm (0 = none)."""

    _attr_native_unit_of_measurement = "cm"
    _attr_icon = "mdi:stairs"
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: RVLevelCoordinator, entry: ConfigEntry, corner: str) -> None:
        super().__init__(coordinator, entry)
        self._corner = corner
        self._attr_translation_key = f"{corner}_chock"
        self._attr_unique_id = f"{entry.entry_id}_{corner}_chock"
        self._object_id_suffix = f"{corner}_chock"

    @property
    def native_value(self) -> float:
        return self.coordinator.data.chock_height_cm[self._corner]

    @property
    def extra_state_attributes(self) -> dict[str, int]:
        return {"chock_index": self.coordinator.data.chock_index[self._corner]}


class RVLevelWheelsToLiftSensor(RVLevelEntity, SensorEntity):
    """How many wheels currently need a chock."""

    _attr_icon = "mdi:counter"
    _attr_translation_key = "wheels_to_lift"

    def __init__(self, coordinator: RVLevelCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_wheels_to_lift"
        self._object_id_suffix = "wheels_to_lift"

    @property
    def native_value(self) -> int:
        return self.coordinator.data.wheels_to_lift


class RVLevelPitchSensor(RVLevelEntity, SensorEntity):
    """Current pitch reading, passed through from the configured pitch sensor."""

    _attr_native_unit_of_measurement = "°"
    _attr_icon = "mdi:angle-acute"
    _attr_suggested_display_precision = 1
    _attr_translation_key = "pitch"

    def __init__(self, coordinator: RVLevelCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_pitch"
        self._object_id_suffix = "pitch"

    @property
    def native_value(self) -> float:
        return self.coordinator.data.pitch

    @property
    def extra_state_attributes(self) -> dict[str, float]:
        return {
            "margin": self._entry.data[CONF_PITCH_MARGIN],
            "residual": self.coordinator.data.residual_pitch,
        }


class RVLevelRollSensor(RVLevelEntity, SensorEntity):
    """Current roll reading, passed through from the configured roll sensor."""

    _attr_native_unit_of_measurement = "°"
    _attr_icon = "mdi:angle-acute"
    _attr_suggested_display_precision = 1
    _attr_translation_key = "roll"

    def __init__(self, coordinator: RVLevelCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_roll"
        self._object_id_suffix = "roll"

    @property
    def native_value(self) -> float:
        return self.coordinator.data.roll

    @property
    def extra_state_attributes(self) -> dict[str, float]:
        return {
            "margin": self._entry.data[CONF_ROLL_MARGIN],
            "residual": self.coordinator.data.residual_roll,
        }
