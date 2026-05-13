from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Ellipse, Line
from kivy.properties import NumericProperty
from kivy.clock import Clock

try:
    from kivy_garden.mapview import MapView, MapMarker
    _MAPVIEW_AVAILABLE = True
except ImportError:
    _MAPVIEW_AVAILABLE = False


# ---------------------------------------------------------------------------
# Fallback stub used on desktop when kivy-garden.mapview is not installed
# ---------------------------------------------------------------------------

class _StubMapView(FloatLayout):
    """Minimal stand-in so the app loads without mapview installed."""

    lat = NumericProperty(25.0330)
    lon = NumericProperty(121.5654)
    zoom = NumericProperty(15)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._pin_pos = None
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *_):
        self.canvas.after.clear()
        with self.canvas.after:
            # Background
            Color(0.18, 0.22, 0.18, 1)
            from kivy.graphics import Rectangle
            Rectangle(pos=self.pos, size=self.size)
            # Grid lines
            Color(0.25, 0.30, 0.25, 1)
            for i in range(0, int(self.width), 40):
                Line(points=[self.x + i, self.y, self.x + i, self.top], width=1)
            for j in range(0, int(self.height), 40):
                Line(points=[self.x, self.y + j, self.right, self.y + j], width=1)
            # Pin
            if self._pin_pos:
                px, py = self._pin_pos
                Color(1, 0.3, 0.3, 1)
                Ellipse(pos=(px - 10, py - 10), size=(20, 20))
                Color(1, 1, 1, 1)
                Ellipse(pos=(px - 4, py - 4), size=(8, 8))

    def center_on(self, lat, lon):
        self.lat = lat
        self.lon = lon

    def set_pin(self, lat, lon):
        # Map lat/lon to pixel position (stub: just centre)
        self._pin_pos = (self.center_x, self.center_y)
        self._redraw()


# ---------------------------------------------------------------------------
# Real MapWidget
# ---------------------------------------------------------------------------

class MapWidget(FloatLayout):
    """
    Wraps kivy-garden.mapview (OSM tiles) with pin management.

    Public API:
        set_pin(lat, lng)          — place/move the location marker
        center_on(lat, lng)        — pan map to coordinates
        on_location_tap(lat, lng)  — override or bind to receive tap events
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._marker = None
        self._long_press_clock = None
        self._long_press_threshold = 0.6  # seconds

        if _MAPVIEW_AVAILABLE:
            self._map = MapView(
                zoom=15,
                lat=25.0330,
                lon=121.5654,
            )
            self._map.bind(on_touch_down=self._on_map_touch_down)
            self._map.bind(on_touch_up=self._on_map_touch_up)
        else:
            self._map = _StubMapView(lat=25.0330, lon=121.5654)

        self.add_widget(self._map)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_pin(self, lat: float, lng: float):
        """Place or move the pin marker to (lat, lng)."""
        if _MAPVIEW_AVAILABLE:
            if self._marker:
                self._map.remove_marker(self._marker)
            self._marker = MapMarker(lat=lat, lon=lng)
            self._map.add_marker(self._marker)
        else:
            self._map.set_pin(lat, lng)

    def center_on(self, lat: float, lng: float):
        """Pan the map to (lat, lng)."""
        if _MAPVIEW_AVAILABLE:
            self._map.center_on(lat, lng)
        else:
            self._map.center_on(lat, lng)

    # ------------------------------------------------------------------
    # Touch → tap detection
    # ------------------------------------------------------------------

    def _on_map_touch_down(self, widget, touch):
        if not self._map.collide_point(*touch.pos):
            return False
        # Start long-press timer
        self._long_press_clock = Clock.schedule_once(
            lambda dt: self._on_long_press(touch), self._long_press_threshold
        )
        return False  # let mapview handle panning too

    def _on_map_touch_up(self, widget, touch):
        if self._long_press_clock:
            self._long_press_clock.cancel()
            self._long_press_clock = None

        # Only treat as tap if finger didn't move much (not a pan)
        if not self._map.collide_point(*touch.pos):
            return False
        dx = abs(touch.x - touch.ox)
        dy = abs(touch.y - touch.oy)
        if dx < 10 and dy < 10:
            if _MAPVIEW_AVAILABLE:
                lat, lng = self._map.get_latlon_at(touch.x, touch.y)
                self.on_location_tap(lat, lng)
        return False

    def _on_long_press(self, touch):
        """Long-press on the map opens coordinate edit (handled by MainScreen)."""
        if _MAPVIEW_AVAILABLE:
            lat, lng = self._map.get_latlon_at(touch.x, touch.y)
            self.on_long_press_tap(lat, lng)

    # ------------------------------------------------------------------
    # Event callbacks — override or bind in parent
    # ------------------------------------------------------------------

    def on_location_tap(self, lat: float, lng: float):
        """Called when user taps the map. Override to handle pin placement."""
        pass

    def on_long_press_tap(self, lat: float, lng: float):
        """Called on long-press. Override to show coordinate edit dialog."""
        pass
