"""Built-in vehicle and chock presets.

Dimensions and chock heights below are community-sourced approximations
meant to give a sane starting point, not certified figures. Always confirm
against your own vehicle's documentation or a tape measure, and against
your chock manufacturer's specs. Corrections and new presets are welcome —
see CONTRIBUTING.md.
"""

from __future__ import annotations

from dataclasses import dataclass

from .const import (
    CUSTOM_PRESET,
    DEFAULT_CHOCK_COUNT,
    DEFAULT_TRACK_WIDTH_CM,
    DEFAULT_WHEELBASE_CM,
)


@dataclass(frozen=True)
class VehiclePreset:
    """A base-vehicle dimension preset."""

    name: str
    wheelbase_cm: float
    track_width_cm: float
    note: str = ""


@dataclass(frozen=True)
class ChockPreset:
    """A leveling-chock (leveler) preset."""

    name: str
    steps_cm: tuple[float, ...]
    default_count: int = DEFAULT_CHOCK_COUNT
    note: str = ""


# Track width uses the front axle figure where front/rear differ, since that
# is what typically limits how the van rocks side to side on chocks.
VEHICLE_PRESETS: dict[str, VehiclePreset] = {
    "ducato_standard": VehiclePreset(
        name="Fiat Ducato / Peugeot Boxer / Citroën Jumper (Standard, 3000 mm)",
        wheelbase_cm=300.0,
        track_width_cm=198.0,
    ),
    "ducato_medium": VehiclePreset(
        name="Fiat Ducato / Peugeot Boxer / Citroën Jumper (Medium, 3450 mm)",
        wheelbase_cm=345.0,
        track_width_cm=198.0,
    ),
    "ducato_maxi": VehiclePreset(
        name="Fiat Ducato / Peugeot Boxer / Citroën Jumper (Maxi, 4035 mm)",
        wheelbase_cm=403.5,
        track_width_cm=198.0,
    ),
    "sprinter_standard": VehiclePreset(
        name="Mercedes-Benz Sprinter (3665 mm)",
        wheelbase_cm=366.5,
        track_width_cm=173.4,
    ),
    "sprinter_long": VehiclePreset(
        name="Mercedes-Benz Sprinter (4325 mm, long)",
        wheelbase_cm=432.5,
        track_width_cm=173.4,
    ),
    "crafter_tge": VehiclePreset(
        name="Volkswagen Crafter / MAN TGE (3640 mm)",
        wheelbase_cm=364.0,
        track_width_cm=185.0,
    ),
    "transit_standard": VehiclePreset(
        name="Ford Transit (3300 mm)",
        wheelbase_cm=330.0,
        track_width_cm=175.0,
    ),
    CUSTOM_PRESET: VehiclePreset(
        name="Custom (enter your own dimensions)",
        wheelbase_cm=DEFAULT_WHEELBASE_CM,
        track_width_cm=DEFAULT_TRACK_WIDTH_CM,
        note="Measure wheelbase (center of front wheel to center of rear wheel) "
        "and track width (center to center of the two wheels on the same axle).",
    ),
}


CHOCK_PRESETS: dict[str, ChockPreset] = {
    "fiamma_kit_level_up": ChockPreset(
        name="Fiamma Kit Level Up",
        steps_cm=(4.0, 7.0, 10.0),
        default_count=2,
        note="Three individual ramps sold as a set (4/7/10 cm); drive each wheel "
        "onto whichever ramp is closest to the height it needs.",
    ),
    "fiamma_level_up": ChockPreset(
        name="Fiamma Level Up (single wedge)",
        steps_cm=(2.0, 4.0, 6.0, 8.0),
        default_count=2,
        note="Approximate — single stackable wedge chock. Please verify against "
        "your exact model and contribute a correction if it differs.",
    ),
    "thule_leveler": ChockPreset(
        name="Thule Leveler",
        steps_cm=(4.5, 9.0),
        default_count=2,
        note="Approximate — interlocking wedge set that can be stacked to roughly "
        "double height. Please verify against your exact set.",
    ),
    CUSTOM_PRESET: ChockPreset(
        name="Custom (enter your own chock heights)",
        steps_cm=(),
        default_count=DEFAULT_CHOCK_COUNT,
        note="Enter the height of each chock/step you own, in centimeters, "
        "separated by commas (e.g. 4, 7, 10).",
    ),
}
