"""
Geocoding helper using the Nominatim API (no API key required).

Supports two input formats:
  1. "lat,lng"  — e.g. "25.0330,121.5654"
  2. Address string — e.g. "台北101"
"""

import re
import threading
from typing import Callable, Optional, Tuple

try:
    import requests
    _REQUESTS_AVAILABLE = True
except ImportError:
    _REQUESTS_AVAILABLE = False

NOMINATIM_URL = 'https://nominatim.openstreetmap.org/search'
HEADERS = {'User-Agent': 'FakeGPSApp/1.0'}
TIMEOUT = 8  # seconds

LatLng = Tuple[float, float]


def _parse_latlng(text: str) -> Optional[LatLng]:
    """Return (lat, lng) if text matches 'float,float', else None."""
    m = re.fullmatch(r'\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*', text.strip())
    if m:
        lat, lng = float(m.group(1)), float(m.group(2))
        if -90 <= lat <= 90 and -180 <= lng <= 180:
            return lat, lng
    return None


def geocode(
    query: str,
    on_success: Callable[[float, float], None],
    on_error: Callable[[str], None],
) -> None:
    """
    Resolve a query to (lat, lng) asynchronously.

    Calls on_success(lat, lng) or on_error(message) on the calling thread
    via Kivy's Clock to keep UI updates thread-safe.
    """
    from kivy.clock import Clock

    # Fast path: raw coordinates
    coords = _parse_latlng(query)
    if coords:
        lat, lng = coords
        Clock.schedule_once(lambda dt: on_success(lat, lng), 0)
        return

    # Slow path: Nominatim lookup in background thread
    def _fetch():
        if not _REQUESTS_AVAILABLE:
            Clock.schedule_once(
                lambda dt: on_error('requests 套件未安裝，無法搜尋地址'), 0
            )
            return
        try:
            resp = requests.get(
                NOMINATIM_URL,
                params={'q': query, 'format': 'json', 'limit': 1},
                headers=HEADERS,
                timeout=TIMEOUT,
            )
            resp.raise_for_status()
            results = resp.json()
            if results:
                lat = float(results[0]['lat'])
                lng = float(results[0]['lon'])
                Clock.schedule_once(lambda dt: on_success(lat, lng), 0)
            else:
                Clock.schedule_once(
                    lambda dt: on_error(f'找不到地點：{query}'), 0
                )
        except Exception as exc:
            Clock.schedule_once(
                lambda dt: on_error(f'搜尋失敗：{exc}'), 0
            )

    threading.Thread(target=_fetch, daemon=True).start()
