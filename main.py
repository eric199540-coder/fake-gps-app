import logging

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder
from kivy.clock import Clock

from logic.app_state import AppState
from logic.location_logic import calculate_next_position
from logic.mock_location_bridge import MockLocationBridge, check_and_request_permissions

# Register KV rules for custom widgets before loading the main layout
from ui.speed_panel import SpeedPanel        # noqa: F401
from ui.search_bar import SearchBar          # noqa: F401
from ui.map_widget import MapWidget          # noqa: F401
from ui.joystick_widget import JoystickWidget  # noqa: F401

Builder.load_file('ui/main_screen.kv')

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

UPDATE_INTERVAL = 0.5  # seconds


class MainScreen(BoxLayout):
    pass


class FakeGPSApp(App):

    def build(self):
        self.state = AppState()
        self.bridge = MockLocationBridge()
        self._update_event = None

        screen = MainScreen()
        self._screen = screen

        # Wire: speed panel → AppState
        screen.ids.speed_panel.bind(
            speed_kmh=lambda _, v: setattr(self.state, 'speed_kmh', v)
        )

        # Wire: joystick → AppState
        joystick = screen.ids.joystick
        joystick.bind(
            dx=lambda _, v: setattr(self.state, 'joystick_dx', v),
            dy=lambda _, v: setattr(self.state, 'joystick_dy', v),
        )

        # Wire: map tap → pin + AppState
        map_widget = screen.ids.map_widget
        map_widget.on_location_tap = self._on_map_tap
        map_widget.on_long_press_tap = self._on_long_press

        # Wire: search bar → map + AppState
        screen.ids.search_bar.bind(
            on_search_result=self._on_search_result,
            on_search_error=self._on_search_error,
        )

        # Request permissions on Android
        check_and_request_permissions()

        # Set initial pin
        map_widget.set_pin(self.state.current_lat, self.state.current_lng)
        self._update_coord_label()

        return screen

    # ------------------------------------------------------------------
    # Mock toggle
    # ------------------------------------------------------------------

    def toggle_mock(self):
        if self.state.is_mocking:
            self._stop_mock()
        else:
            self._start_mock()

    def _start_mock(self):
        ok = self.bridge.start_mock(self.state.current_lat, self.state.current_lng)
        if ok:
            self.state.is_mocking = True
            self._update_event = Clock.schedule_interval(self._tick, UPDATE_INTERVAL)
            self._screen.ids.toggle_btn.text = '停止模擬'
            self._screen.ids.toggle_btn.background_color = (0.8, 0.2, 0.2, 1)
            self._screen.ids.status_label.text = '狀態：模擬中 ●'
            self._screen.ids.status_label.color = (0.3, 1.0, 0.3, 1)
            log.info("Mock started")

    def _stop_mock(self):
        if self._update_event:
            self._update_event.cancel()
            self._update_event = None
        self.bridge.stop_mock()
        self.state.is_mocking = False
        self._screen.ids.toggle_btn.text = '開始模擬'
        self._screen.ids.toggle_btn.background_color = (0.2, 0.7, 0.3, 1)
        self._screen.ids.status_label.text = '狀態：已停止'
        self._screen.ids.status_label.color = (0.7, 0.7, 0.7, 1)
        log.info("Mock stopped")

    # ------------------------------------------------------------------
    # 500 ms update tick (Requirements 3.1, 3.2, 3.4)
    # ------------------------------------------------------------------

    def _tick(self, dt):
        dx = self.state.joystick_dx
        dy = self.state.joystick_dy

        # Only move if joystick is deflected
        if abs(dx) > 1e-6 or abs(dy) > 1e-6:
            new_lat, new_lng = calculate_next_position(
                self.state.current_lat,
                self.state.current_lng,
                dx, dy,
                self.state.speed_kmh,
                dt,
            )
            self.state.current_lat = new_lat
            self.state.current_lng = new_lng

            # Push to Android service
            self.bridge.update_location(new_lat, new_lng)

            # Update map marker
            self._screen.ids.map_widget.set_pin(new_lat, new_lng)
            self._screen.ids.map_widget.center_on(new_lat, new_lng)

        self._update_coord_label()

    # ------------------------------------------------------------------
    # Map interaction handlers
    # ------------------------------------------------------------------

    def _on_map_tap(self, lat: float, lng: float):
        """User tapped the map — move pin and update mock location."""
        self.state.current_lat = lat
        self.state.current_lng = lng
        self._screen.ids.map_widget.set_pin(lat, lng)
        if self.state.is_mocking:
            self.bridge.update_location(lat, lng)
        self._update_coord_label()

    def _on_long_press(self, lat: float, lng: float):
        """Long-press on map — open coordinate edit popup."""
        from ui.coord_edit_popup import CoordEditPopup
        popup = CoordEditPopup(
            lat=self.state.current_lat,
            lng=self.state.current_lng,
            on_confirm=self._on_coord_edit_confirm,
        )
        popup.open()

    def _on_coord_edit_confirm(self, lat: float, lng: float):
        self._on_map_tap(lat, lng)

    # ------------------------------------------------------------------
    # Search bar handlers
    # ------------------------------------------------------------------

    def _on_search_result(self, _, lat: float, lng: float):
        self._on_map_tap(lat, lng)
        self._screen.ids.map_widget.center_on(lat, lng)

    def _on_search_error(self, _, msg: str):
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label
        popup = Popup(
            title='搜尋失敗',
            content=Label(text=msg),
            size_hint=(0.8, None),
            height='160dp',
        )
        popup.open()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _update_coord_label(self):
        self._screen.ids.coord_label.text = (
            f'緯度：{self.state.current_lat:.6f}\n'
            f'經度：{self.state.current_lng:.6f}'
        )

    def on_stop(self):
        """Clean up when app closes."""
        if self.state.is_mocking:
            self._stop_mock()


if __name__ == '__main__':
    FakeGPSApp().run()
