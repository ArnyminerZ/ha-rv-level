"""Constants for the RV Level integration."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "rv_level"
PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]

# --- Config / options keys -------------------------------------------------

CONF_PITCH_ENTITY = "pitch_entity"
CONF_ROLL_ENTITY = "roll_entity"

CONF_VEHICLE_PRESET = "vehicle_preset"
CONF_WHEELBASE = "wheelbase"
CONF_TRACK_WIDTH = "track_width"

CONF_PITCH_MARGIN = "pitch_margin"
CONF_ROLL_MARGIN = "roll_margin"

CONF_CHOCK_PRESET = "chock_preset"
CONF_CHOCK_STEPS = "chock_steps"
CONF_CHOCK_COUNT = "chock_count"

CUSTOM_PRESET = "custom"

# --- Defaults ---------------------------------------------------------------

DEFAULT_WHEELBASE_CM = 350.0
DEFAULT_TRACK_WIDTH_CM = 175.0
DEFAULT_PITCH_MARGIN_DEG = 1.5
DEFAULT_ROLL_MARGIN_DEG = 1.5
DEFAULT_CHOCK_COUNT = 2

# --- Corners ------------------------------------------------------------

CORNERS = ("front_left", "front_right", "rear_left", "rear_right")
