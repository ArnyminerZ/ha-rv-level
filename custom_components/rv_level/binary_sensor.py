"""Binary sensor entities for RV Level."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import RVLevelCoordinator
from .entity import RVLevelEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up RV Level binary sensors for a config entry."""
    coordinator: RVLevelCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            RVLevelIsLevelSensor(coordinator, entry),
            RVLevelLevelableSensor(coordinator, entry),
        ]
    )


class RVLevelIsLevelSensor(RVLevelEntity, BinarySensorEntity):
    """Whether the vehicle is currently level, right now, with no chocks."""

    _attr_icon = "mdi:spirit-level"
    _attr_translation_key = "level"

    def __init__(self, coordinator: RVLevelCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_level"
        self._object_id_suffix = "level"

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.is_level


class RVLevelLevelableSensor(RVLevelEntity, BinarySensorEntity):
    """Whether the configured chocks can bring the vehicle within margins."""

    _attr_icon = "mdi:check-decagram"
    _attr_translation_key = "levelable"

    def __init__(self, coordinator: RVLevelCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_levelable"
        self._object_id_suffix = "levelable"

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.levelable
