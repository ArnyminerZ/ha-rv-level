"""Shared entity base class for RV Level."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import RVLevelCoordinator


class RVLevelEntity(CoordinatorEntity[RVLevelCoordinator]):
    """Base entity tying every RV Level entity to the same device."""

    _attr_has_entity_name = True

    # Fixed, non-translated object-id suffix (e.g. "front_left_lift"), set by
    # each subclass's __init__. Kept separate from `_attr_translation_key` /
    # the entity's display `name` on purpose: see `suggested_object_id` below.
    _object_id_suffix: str | None = None

    def __init__(self, coordinator: RVLevelCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="RV Level (community)",
            model="Pitch/roll leveling calculator",
        )

    @property
    def suggested_object_id(self) -> str | None:
        """Keep newly-created entity_ids in English regardless of display language.

        By default Home Assistant derives a new entity's entity_id from its
        (possibly translated) display name, and does so *in the configured
        language* for a large set of languages -- including Catalan and
        Spanish, which this integration ships translations for (see
        `homeassistant.generated.languages.NATIVE_ENTITY_IDS`). Our own
        dashboard cards, recorder-exclude examples, and this repo's README
        all key off a fixed English suffix (e.g. `_front_left_lift`), so the
        entity_id must not change based on the user's language -- only the
        display name should.
        """
        return self._object_id_suffix
