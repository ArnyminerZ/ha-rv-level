"""Unit tests for the leveling solver.

These only exercise custom_components/rv_level/solver.py, which has no
Home Assistant imports, so they run with plain pytest and no test harness.
"""

from custom_components.rv_level.solver import solve

WHEELBASE = 350.0
TRACK_WIDTH = 175.0
MARGIN = 1.5
STEPS = [4.0, 7.0, 10.0]


def test_already_level_needs_no_chocks():
    result = solve(0.5, -0.3, WHEELBASE, TRACK_WIDTH, MARGIN, MARGIN, STEPS, 2)
    assert result.is_level
    assert result.levelable
    assert result.wheels_to_lift == 0
    assert all(v == 0 for v in result.chock_height_cm.values())


def test_pitch_only_lifts_two_wheels_and_is_levelable():
    result = solve(2.0, 0.0, WHEELBASE, TRACK_WIDTH, MARGIN, MARGIN, STEPS, 2)
    assert not result.is_level
    assert result.wheels_to_lift == 2
    assert result.levelable
    assert result.chock_height_cm["front_left"] == result.chock_height_cm["front_right"]
    assert result.chock_height_cm["rear_left"] == 0
    assert result.chock_height_cm["rear_right"] == 0


def test_both_axes_out_need_three_wheels_not_levelable_with_two_chocks():
    result = solve(3.0, 3.0, WHEELBASE, TRACK_WIDTH, MARGIN, MARGIN, STEPS, 2)
    assert result.wheels_to_lift == 3
    assert not result.levelable


def test_both_axes_out_is_levelable_with_enough_chocks():
    result = solve(1.6, 1.6, WHEELBASE, TRACK_WIDTH, MARGIN, MARGIN, STEPS, 3)
    assert result.wheels_to_lift == 3
    assert result.levelable


def test_extreme_tilt_exceeds_max_chock_height_and_is_not_levelable():
    result = solve(10.0, 0.0, WHEELBASE, TRACK_WIDTH, MARGIN, MARGIN, STEPS, 2)
    assert not result.levelable
    assert result.chock_height_cm["front_left"] == max(STEPS)


def test_signs_pick_the_correct_low_corners():
    # Front low, left low -> front-left gets both corrections, rear-right gets none.
    result = solve(2.0, 2.0, WHEELBASE, TRACK_WIDTH, MARGIN, MARGIN, STEPS, 4)
    assert result.lift_cm["front_left"] > result.lift_cm["front_right"]
    assert result.lift_cm["front_left"] > result.lift_cm["rear_left"]
    assert result.lift_cm["rear_right"] == 0

    # Flip both signs -> rear-right should now be the corner needing the most lift.
    flipped = solve(-2.0, -2.0, WHEELBASE, TRACK_WIDTH, MARGIN, MARGIN, STEPS, 4)
    assert flipped.lift_cm["rear_right"] > flipped.lift_cm["rear_left"]
    assert flipped.lift_cm["rear_right"] > flipped.lift_cm["front_right"]
    assert flipped.lift_cm["front_left"] == 0


def test_bubble_position_tracks_pitch_and_roll_sign():
    result = solve(3.0, -3.0, WHEELBASE, TRACK_WIDTH, MARGIN, MARGIN, STEPS, 2, bubble_max_angle=6.0)
    assert result.bubble_y > 0
    assert result.bubble_x < 0
