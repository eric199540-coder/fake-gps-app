import math

from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Line
from kivy.properties import NumericProperty, BooleanProperty
from kivy.event import EventDispatcher


class JoystickWidget(Widget):
    """
    Virtual joystick with an outer ring (base) and an inner knob.

    Outputs:
        dx (float): East/west deflection in [-1.0, 1.0]  (positive = east)
        dy (float): North/south deflection in [-1.0, 1.0] (positive = north)

    Events:
        on_move(dx, dy): Fired every touch-move while the knob is active.
        on_release():    Fired when the finger lifts; dx/dy reset to 0.
    """

    dx = NumericProperty(0.0)
    dy = NumericProperty(0.0)
    active = BooleanProperty(False)

    # Visual proportions
    OUTER_RATIO = 0.90   # outer ring diameter relative to widget size
    KNOB_RATIO  = 0.38   # knob diameter relative to widget size

    def __init__(self, **kwargs):
        self.register_event_type('on_move')
        self.register_event_type('on_release')
        super().__init__(**kwargs)
        self._touch_uid = None
        self.bind(pos=self._redraw, size=self._redraw)

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _redraw(self, *_):
        self.canvas.clear()
        cx, cy = self.center
        r_outer = min(self.width, self.height) * self.OUTER_RATIO / 2
        r_knob  = min(self.width, self.height) * self.KNOB_RATIO  / 2

        # Knob position (offset from centre by current dx/dy)
        max_offset = r_outer - r_knob
        kx = cx + self.dx * max_offset
        ky = cy + self.dy * max_offset

        with self.canvas:
            # Outer ring background
            Color(0.2, 0.2, 0.2, 0.55)
            Ellipse(
                pos=(cx - r_outer, cy - r_outer),
                size=(r_outer * 2, r_outer * 2),
            )
            # Outer ring border
            Color(0.6, 0.6, 0.6, 0.9)
            Line(
                circle=(cx, cy, r_outer),
                width=2,
            )
            # Knob
            Color(0.3, 0.7, 1.0, 0.95)
            Ellipse(
                pos=(kx - r_knob, ky - r_knob),
                size=(r_knob * 2, r_knob * 2),
            )

    # ------------------------------------------------------------------
    # Touch handling
    # ------------------------------------------------------------------

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        if self._touch_uid is not None:
            return False  # already tracking one finger
        self._touch_uid = touch.uid
        self.active = True
        self._update_vector(touch.x, touch.y)
        return True

    def on_touch_move(self, touch):
        if touch.uid != self._touch_uid:
            return False
        self._update_vector(touch.x, touch.y)
        return True

    def on_touch_up(self, touch):
        if touch.uid != self._touch_uid:
            return False
        self._touch_uid = None
        self.active = False
        self.dx = 0.0
        self.dy = 0.0
        self._redraw()
        self.dispatch('on_release')
        return True

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _update_vector(self, tx: float, ty: float):
        cx, cy = self.center
        raw_dx = tx - cx
        raw_dy = ty - cy
        magnitude = math.sqrt(raw_dx ** 2 + raw_dy ** 2)

        r_outer = min(self.width, self.height) * self.OUTER_RATIO / 2
        r_knob  = min(self.width, self.height) * self.KNOB_RATIO  / 2
        max_offset = r_outer - r_knob

        if magnitude < 1e-6:
            self.dx = 0.0
            self.dy = 0.0
        elif magnitude <= max_offset:
            self.dx = raw_dx / max_offset
            self.dy = raw_dy / max_offset
        else:
            # Clamp to unit circle
            self.dx = raw_dx / magnitude
            self.dy = raw_dy / magnitude

        self._redraw()
        self.dispatch('on_move', self.dx, self.dy)

    # ------------------------------------------------------------------
    # Default event handlers (required by Kivy)
    # ------------------------------------------------------------------

    def on_move(self, dx, dy):
        pass

    def on_release(self):
        pass
