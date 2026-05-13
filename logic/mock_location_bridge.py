"""
Bridge between Python and the Android MockLocationService.

On Android (Pyjnius available): calls the Java service directly.
On desktop (no Pyjnius): logs calls so the rest of the app still runs.

Requirements: 1.3, 1.4, 5.3
"""

import logging

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Platform detection
# ---------------------------------------------------------------------------

try:
    from jnius import autoclass
    from android.permissions import request_permissions, Permission  # type: ignore
    _ON_ANDROID = True
except ImportError:
    _ON_ANDROID = False


# ---------------------------------------------------------------------------
# Permission check / request
# ---------------------------------------------------------------------------

def check_and_request_permissions(on_result=None):
    """
    Request ACCESS_FINE_LOCATION and ACCESS_MOCK_LOCATION on Android.
    on_result(granted: bool) is called after the user responds.
    """
    if not _ON_ANDROID:
        log.debug("Permission check skipped (not on Android)")
        if on_result:
            on_result(True)
        return

    def _callback(permissions, grants):
        granted = all(grants)
        if not granted:
            _show_permission_dialog()
        if on_result:
            on_result(granted)

    request_permissions(
        [Permission.ACCESS_FINE_LOCATION],
        _callback,
    )


def _show_permission_dialog():
    """Show a Kivy popup guiding the user to Developer Options."""
    from kivy.uix.popup import Popup
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.label import Label
    from kivy.uix.button import Button

    content = BoxLayout(orientation='vertical', spacing='8dp', padding='12dp')
    content.add_widget(Label(
        text=(
            '需要「模擬位置」權限。\n\n'
            '請前往：\n'
            '設定 → 開發人員選項 → 選取模擬位置應用程式\n'
            '並選擇本應用程式。'
        ),
        halign='center',
    ))
    popup = Popup(
        title='需要權限',
        content=content,
        size_hint=(0.88, None),
        height='260dp',
    )
    btn = Button(text='我知道了', size_hint_y=None, height='40dp')
    btn.bind(on_release=popup.dismiss)
    content.add_widget(btn)
    popup.open()


# ---------------------------------------------------------------------------
# Mock location bridge
# ---------------------------------------------------------------------------

class MockLocationBridge:
    """
    Thin wrapper around MockLocationService.

    Usage:
        bridge = MockLocationBridge()
        bridge.start_mock(25.033, 121.565)
        bridge.update_location(25.034, 121.566)
        bridge.stop_mock()
    """

    def __init__(self):
        self._service = None
        self._context = None
        self._active = False

        if _ON_ANDROID:
            try:
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                self._context = PythonActivity.mActivity
                self._service = autoclass('com.fakegps.MockLocationService')
            except Exception as exc:
                log.error("Failed to load MockLocationService: %s", exc)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start_mock(self, lat: float, lng: float) -> bool:
        """
        Start the Foreground Service and begin injecting (lat, lng).
        Returns True if started successfully.
        """
        if _ON_ANDROID and self._service and self._context:
            try:
                self._service.startMock(self._context, lat, lng)
                self._active = True
                log.info("Mock started at %.6f, %.6f", lat, lng)
                return True
            except Exception as exc:
                log.error("start_mock failed: %s", exc)
                return False
        else:
            log.debug("[STUB] start_mock(%.6f, %.6f)", lat, lng)
            self._active = True
            return True

    def update_location(self, lat: float, lng: float) -> None:
        """Push a new coordinate to the running service."""
        if _ON_ANDROID and self._service:
            try:
                self._service.setLocation(lat, lng)
            except Exception as exc:
                log.error("update_location failed: %s", exc)
        else:
            log.debug("[STUB] update_location(%.6f, %.6f)", lat, lng)

    def stop_mock(self) -> None:
        """Stop the Foreground Service and restore real GPS."""
        if _ON_ANDROID and self._service and self._context:
            try:
                self._service.stopMock(self._context)
            except Exception as exc:
                log.error("stop_mock failed: %s", exc)
        else:
            log.debug("[STUB] stop_mock()")
        self._active = False

    @property
    def is_active(self) -> bool:
        return self._active
