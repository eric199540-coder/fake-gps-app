import math

EARTH_RADIUS_M = 6_371_000.0  # Earth mean radius in metres


def clamp_coordinates(lat: float, lng: float) -> tuple[float, float]:
    """Clamp lat/lng to valid WGS-84 ranges."""
    lat = max(-90.0, min(90.0, lat))
    lng = max(-180.0, min(180.0, lng))
    return lat, lng


def offset_coordinate(
    lat: float, lng: float, distance_m: float, bearing_rad: float
) -> tuple[float, float]:
    """
    Calculate a new coordinate given a starting point, distance, and bearing.

    Uses the spherical-earth (Haversine) direct formula.

    Args:
        lat: Starting latitude in degrees.
        lng: Starting longitude in degrees.
        distance_m: Distance to travel in metres.
        bearing_rad: Direction of travel in radians (0 = north, π/2 = east).

    Returns:
        (new_lat, new_lng) in degrees, clamped to valid ranges.
    """
    lat_rad = math.radians(lat)
    lng_rad = math.radians(lng)

    angular_dist = distance_m / EARTH_RADIUS_M  # central angle in radians

    new_lat_rad = math.asin(
        math.sin(lat_rad) * math.cos(angular_dist)
        + math.cos(lat_rad) * math.sin(angular_dist) * math.cos(bearing_rad)
    )

    new_lng_rad = lng_rad + math.atan2(
        math.sin(bearing_rad) * math.sin(angular_dist) * math.cos(lat_rad),
        math.cos(angular_dist) - math.sin(lat_rad) * math.sin(new_lat_rad),
    )

    new_lat = math.degrees(new_lat_rad)
    new_lng = math.degrees(new_lng_rad)

    # Normalise longitude to [-180, 180]
    new_lng = (new_lng + 180.0) % 360.0 - 180.0

    return clamp_coordinates(new_lat, new_lng)


def calculate_next_position(
    lat: float,
    lng: float,
    dx: float,
    dy: float,
    speed_kmh: float,
    delta_time_s: float,
) -> tuple[float, float]:
    """
    Calculate the next GPS position based on joystick input and speed.

    Args:
        lat: Current latitude in degrees.
        lng: Current longitude in degrees.
        dx: Joystick east/west component in [-1.0, 1.0]  (positive = east).
        dy: Joystick north/south component in [-1.0, 1.0] (positive = north).
        speed_kmh: Movement speed in km/h.
        delta_time_s: Time elapsed since last update in seconds.

    Returns:
        (new_lat, new_lng) in degrees.
    """
    # If joystick is centred, stay put
    magnitude = math.sqrt(dx * dx + dy * dy)
    if magnitude < 1e-6:
        return lat, lng

    # Normalise direction vector
    norm_dx = dx / magnitude
    norm_dy = dy / magnitude

    # Convert speed to metres per tick
    speed_ms = speed_kmh / 3.6
    distance_m = speed_ms * delta_time_s * magnitude  # scale by stick deflection

    # bearing: atan2(east, north) — matches standard navigation convention
    bearing_rad = math.atan2(norm_dx, norm_dy)

    return offset_coordinate(lat, lng, distance_m, bearing_rad)
