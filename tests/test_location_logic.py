import math
import sys
import os

# Allow running tests from the project root without installing the package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from logic.location_logic import (
    offset_coordinate,
    calculate_next_position,
    clamp_coordinates,
    EARTH_RADIUS_M,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def approx_equal(a: float, b: float, tol: float = 1e-6) -> bool:
    return abs(a - b) <= tol


def haversine_distance(lat1, lng1, lat2, lng2) -> float:
    """Return great-circle distance in metres between two WGS-84 points."""
    R = EARTH_RADIUS_M
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


# ---------------------------------------------------------------------------
# clamp_coordinates
# ---------------------------------------------------------------------------

class TestClampCoordinates:
    def test_valid_coords_unchanged(self):
        lat, lng = clamp_coordinates(25.0, 121.0)
        assert lat == 25.0 and lng == 121.0

    def test_lat_clamped_above(self):
        lat, _ = clamp_coordinates(95.0, 0.0)
        assert lat == 90.0

    def test_lat_clamped_below(self):
        lat, _ = clamp_coordinates(-95.0, 0.0)
        assert lat == -90.0

    def test_lng_clamped_above(self):
        _, lng = clamp_coordinates(0.0, 185.0)
        assert lng == 180.0

    def test_lng_clamped_below(self):
        _, lng = clamp_coordinates(0.0, -185.0)
        assert lng == -180.0


# ---------------------------------------------------------------------------
# offset_coordinate
# ---------------------------------------------------------------------------

class TestOffsetCoordinate:
    def test_north_moves_lat_up(self):
        lat, lng = offset_coordinate(0.0, 0.0, 1000.0, 0.0)  # bearing 0 = north
        assert lat > 0.0
        assert approx_equal(lng, 0.0, tol=1e-4)

    def test_south_moves_lat_down(self):
        lat, lng = offset_coordinate(0.0, 0.0, 1000.0, math.pi)  # bearing π = south
        assert lat < 0.0

    def test_east_moves_lng_right(self):
        lat, lng = offset_coordinate(0.0, 0.0, 1000.0, math.pi / 2)  # bearing π/2 = east
        assert lng > 0.0
        assert approx_equal(lat, 0.0, tol=1e-4)

    def test_west_moves_lng_left(self):
        lat, lng = offset_coordinate(0.0, 0.0, 1000.0, -math.pi / 2)  # bearing -π/2 = west
        assert lng < 0.0

    def test_distance_accuracy(self):
        """Travelling 1 km north should land ~1000 m away."""
        new_lat, new_lng = offset_coordinate(0.0, 0.0, 1000.0, 0.0)
        dist = haversine_distance(0.0, 0.0, new_lat, new_lng)
        assert abs(dist - 1000.0) < 1.0  # within 1 m

    def test_zero_distance_returns_same_point(self):
        lat, lng = offset_coordinate(25.0, 121.0, 0.0, 0.0)
        assert approx_equal(lat, 25.0) and approx_equal(lng, 121.0)


# ---------------------------------------------------------------------------
# calculate_next_position
# ---------------------------------------------------------------------------

class TestCalculateNextPosition:
    def test_zero_joystick_no_movement(self):
        lat, lng = calculate_next_position(25.0, 121.0, 0.0, 0.0, 10.0, 0.5)
        assert lat == 25.0 and lng == 121.0

    def test_north_joystick_increases_lat(self):
        lat, lng = calculate_next_position(25.0, 121.0, 0.0, 1.0, 10.0, 0.5)
        assert lat > 25.0
        assert approx_equal(lng, 121.0, tol=1e-4)

    def test_east_joystick_increases_lng(self):
        lat, lng = calculate_next_position(0.0, 0.0, 1.0, 0.0, 10.0, 0.5)
        assert lng > 0.0
        assert approx_equal(lat, 0.0, tol=1e-4)

    def test_speed_scales_distance(self):
        """Doubling speed should roughly double the distance travelled."""
        lat1, lng1 = calculate_next_position(0.0, 0.0, 0.0, 1.0, 10.0, 0.5)
        lat2, lng2 = calculate_next_position(0.0, 0.0, 0.0, 1.0, 20.0, 0.5)
        dist1 = haversine_distance(0.0, 0.0, lat1, lng1)
        dist2 = haversine_distance(0.0, 0.0, lat2, lng2)
        assert abs(dist2 / dist1 - 2.0) < 0.01

    def test_speed_conversion_10kmh_half_second(self):
        """10 km/h for 0.5 s should move ~1.389 m."""
        expected_m = (10.0 / 3.6) * 0.5  # ≈ 1.389 m
        lat, lng = calculate_next_position(0.0, 0.0, 0.0, 1.0, 10.0, 0.5)
        dist = haversine_distance(0.0, 0.0, lat, lng)
        assert abs(dist - expected_m) < 0.01

    def test_partial_joystick_deflection_scales_speed(self):
        """Half deflection (0.5) should travel half the distance of full deflection (1.0)."""
        lat_full, lng_full = calculate_next_position(0.0, 0.0, 0.0, 1.0, 10.0, 0.5)
        lat_half, lng_half = calculate_next_position(0.0, 0.0, 0.0, 0.5, 10.0, 0.5)
        dist_full = haversine_distance(0.0, 0.0, lat_full, lng_full)
        dist_half = haversine_distance(0.0, 0.0, lat_half, lng_half)
        assert abs(dist_half / dist_full - 0.5) < 0.01
