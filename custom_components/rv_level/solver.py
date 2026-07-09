"""Leveling solver for RV Level.

The vehicle is modelled as a rigid plane. For small angles, the height of a
point at longitudinal offset x and lateral offset y from a reference corner
is z = x * tan(pitch) + y * tan(roll). That relation is linear in x and y, so
the pitch and roll corrections can be computed independently ("axes" below
refers to this decomposition, not to a physical vehicle axle) and summed per
corner to get the raw lift every wheel would need to bring the chassis dead
level.

Physical chocks only come in fixed heights (the configured "steps"), and only
a limited number of them is available, so the raw lift is then matched to the
nearest available chock height, per corner, prioritizing the corners that
need the most lift when chocks are scarce. The residual tilt that is left
over after placing those chocks is computed the same way a real rigid plane
would settle: by comparing the front/rear and left/right averages of the
*achieved* corner heights, not just by looking at each corner in isolation.
That residual is what "levelable" is based on, so it automatically accounts
for both a limited chock count and a maximum chock height, without special
casing either.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

FRONT_LEFT = "front_left"
FRONT_RIGHT = "front_right"
REAR_LEFT = "rear_left"
REAR_RIGHT = "rear_right"
CORNERS = (FRONT_LEFT, FRONT_RIGHT, REAR_LEFT, REAR_RIGHT)


@dataclass
class LevelResult:
    """Result of a single solve() call."""

    pitch: float
    roll: float
    lift_cm: dict[str, float]
    chock_height_cm: dict[str, float]
    chock_index: dict[str, int]
    wheels_to_lift: int
    is_level: bool
    levelable: bool
    residual_pitch: float
    residual_roll: float


def _nearest_level(height: float, steps: list[float]) -> tuple[int, float]:
    """Return (index, height) of the chock level closest to `height`.

    Index/height 0 means "no chock". `steps` must already be sorted
    ascending. Index is 1-based into `steps` when a chock is selected.
    """
    levels = (0.0, *steps)
    best_index = 0
    best_diff = abs(height - levels[0])
    for index, level in enumerate(levels[1:], start=1):
        diff = abs(height - level)
        if diff < best_diff:
            best_index, best_diff = index, diff
    return best_index, levels[best_index]


def solve(
    pitch: float,
    roll: float,
    wheelbase_cm: float,
    track_width_cm: float,
    pitch_margin: float,
    roll_margin: float,
    chock_steps_cm: list[float],
    chock_count: int,
) -> LevelResult:
    """Compute per-corner lift/chock choices for the given pitch/roll reading."""
    steps = sorted(s for s in chock_steps_cm if s > 0)

    pitch_out = abs(pitch) > pitch_margin
    roll_out = abs(roll) > roll_margin
    raw_is_level = not pitch_out and not roll_out

    pitch_lift = wheelbase_cm * math.tan(math.radians(abs(pitch))) if pitch_out else 0.0
    roll_lift = track_width_cm * math.tan(math.radians(abs(roll))) if roll_out else 0.0

    front_low = pitch > 0
    left_low = roll > 0

    ideal_lift = {
        FRONT_LEFT: (roll_lift if left_low else 0.0) + (pitch_lift if front_low else 0.0),
        FRONT_RIGHT: (roll_lift if not left_low else 0.0) + (pitch_lift if front_low else 0.0),
        REAR_LEFT: (roll_lift if left_low else 0.0) + (pitch_lift if not front_low else 0.0),
        REAR_RIGHT: (roll_lift if not left_low else 0.0) + (pitch_lift if not front_low else 0.0),
    }

    desired = {corner: _nearest_level(ideal_lift[corner], steps) for corner in CORNERS}
    wheels_to_lift = sum(1 for _, height in desired.values() if height > 0)

    # If there are fewer chocks than wheels that need one, favor the corners
    # that need the most lift; the rest are left un-chocked.
    priority = sorted(
        (corner for corner in CORNERS if desired[corner][1] > 0),
        key=lambda corner: ideal_lift[corner],
        reverse=True,
    )
    chocked = set(priority[: max(chock_count, 0)])

    chock_index: dict[str, int] = {}
    chock_height: dict[str, float] = {}
    for corner in CORNERS:
        if corner in chocked:
            chock_index[corner], chock_height[corner] = desired[corner]
        else:
            chock_index[corner], chock_height[corner] = 0, 0.0

    front_achieved = (chock_height[FRONT_LEFT] + chock_height[FRONT_RIGHT]) / 2
    rear_achieved = (chock_height[REAR_LEFT] + chock_height[REAR_RIGHT]) / 2
    left_achieved = (chock_height[FRONT_LEFT] + chock_height[REAR_LEFT]) / 2
    right_achieved = (chock_height[FRONT_RIGHT] + chock_height[REAR_RIGHT]) / 2

    achieved_pitch_diff = (
        (front_achieved - rear_achieved) if front_low else (rear_achieved - front_achieved)
    )
    achieved_roll_diff = (
        (left_achieved - right_achieved) if left_low else (right_achieved - left_achieved)
    )

    residual_pitch = (
        math.degrees(math.atan(abs(pitch_lift - achieved_pitch_diff) / wheelbase_cm))
        if pitch_out and wheelbase_cm > 0
        else 0.0
    )
    residual_roll = (
        math.degrees(math.atan(abs(roll_lift - achieved_roll_diff) / track_width_cm))
        if roll_out and track_width_cm > 0
        else 0.0
    )

    levelable = residual_pitch <= pitch_margin and residual_roll <= roll_margin

    return LevelResult(
        pitch=round(pitch, 2),
        roll=round(roll, 2),
        lift_cm={corner: round(ideal_lift[corner], 1) for corner in CORNERS},
        chock_height_cm={corner: round(chock_height[corner], 1) for corner in CORNERS},
        chock_index=chock_index,
        wheels_to_lift=wheels_to_lift,
        is_level=raw_is_level,
        levelable=levelable,
        residual_pitch=round(residual_pitch, 2),
        residual_roll=round(residual_roll, 2),
    )
