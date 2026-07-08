"""Sensor entities for RV Level."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_PITCH_MARGIN, CONF_ROLL_MARGIN, CORNER_NAMES, DOMAIN
from .coordinator import RVLevelCoordinator
from .entity import RVLevelEntity
from .solver import DEFAULT_BUBBLE_MAX_ANGLE


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up RV Level sensors for a config entry."""
    coordinator: RVLevelCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []
    for corner, label in CORNER_NAMES.items():
        entities.append(RVLevelLiftSensor(coordinator, entry, corner, label))
        entities.append(RVLevelChockSensor(coordinator, entry, corner, label))
    entities.append(RVLevelWheelsToLiftSensor(coordinator, entry))
    entities.append(RVLevelBubbleSensor(coordinator, entry))

    async_add_entities(entities)


class RVLevelLiftSensor(RVLevelEntity, SensorEntity):
    """How much a given wheel needs to be raised, in cm."""

    _attr_native_unit_of_measurement = "cm"
    _attr_icon = "mdi:arrow-up-bold-box"
    _attr_suggested_display_precision = 1

    def __init__(
        self, coordinator: RVLevelCoordinator, entry: ConfigEntry, corner: str, label: str
    ) -> None:
        super().__init__(coordinator, entry)
        self._corner = corner
        self._attr_name = f"{label} lift"
        self._attr_unique_id = f"{entry.entry_id}_{corner}_lift"

    @property
    def native_value(self) -> float:
        return self.coordinator.data.lift_cm[self._corner]


class RVLevelChockSensor(RVLevelEntity, SensorEntity):
    """Height of the chock to place under a given wheel, in cm (0 = none)."""

    _attr_native_unit_of_measurement = "cm"
    _attr_icon = "mdi:stairs"
    _attr_suggested_display_precision = 1

    def __init__(
        self, coordinator: RVLevelCoordinator, entry: ConfigEntry, corner: str, label: str
    ) -> None:
        super().__init__(coordinator, entry)
        self._corner = corner
        self._attr_name = f"{label} chock"
        self._attr_unique_id = f"{entry.entry_id}_{corner}_chock"

    @property
    def native_value(self) -> float:
        return self.coordinator.data.chock_height_cm[self._corner]

    @property
    def extra_state_attributes(self) -> dict[str, int]:
        return {"chock_index": self.coordinator.data.chock_index[self._corner]}


class RVLevelWheelsToLiftSensor(RVLevelEntity, SensorEntity):
    """How many wheels currently need a chock."""

    _attr_icon = "mdi:counter"
    _attr_name = "Wheels to lift"

    def __init__(self, coordinator: RVLevelCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_wheels_to_lift"

    @property
    def native_value(self) -> int:
        return self.coordinator.data.wheels_to_lift


class RVLevelBubbleSensor(RVLevelEntity, SensorEntity):
    """Bubble-level position, exposed as attributes for dashboard cards."""

    _attr_icon = "mdi:circle-slice-8"
    _attr_name = "Bubble position"

    def __init__(self, coordinator: RVLevelCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_bubble"

    @property
    def native_value(self) -> str:
        data = self.coordinator.data
        return f"{data.bubble_x},{data.bubble_y}"

    @property
    def extra_state_attributes(self) -> dict[str, float]:
        data = self.coordinator.data
        entry_data = self._entry.data
        return {
            "x": data.bubble_x,
            "y": data.bubble_y,
            "residual_pitch": data.residual_pitch,
            "residual_roll": data.residual_roll,
            "pitch_margin": entry_data[CONF_PITCH_MARGIN],
            "roll_margin": entry_data[CONF_ROLL_MARGIN],
            "bubble_max_angle": DEFAULT_BUBBLE_MAX_ANGLE,
        }
