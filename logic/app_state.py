from dataclasses import dataclass, field


@dataclass
class AppState:
    """Central state shared across all UI and logic components."""
    current_lat: float = 25.0330   # Default: Taipei 101
    current_lng: float = 121.5654
    speed_kmh: float = 5.0
    is_mocking: bool = False
    joystick_dx: float = 0.0       # [-1.0, 1.0] east/west
    joystick_dy: float = 0.0       # [-1.0, 1.0] north/south
