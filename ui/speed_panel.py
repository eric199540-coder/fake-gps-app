from kivy.uix.boxlayout import BoxLayout
from kivy.properties import NumericProperty, ObjectProperty
from kivy.lang import Builder

Builder.load_string("""
<SpeedPanel>:
    orientation: 'vertical'
    spacing: '4dp'
    padding: '6dp'
    size_hint_y: None
    height: '110dp'

    # Speed label + slider row
    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: '30dp'
        spacing: '8dp'
        Label:
            text: '速度：'
            size_hint_x: None
            width: '52dp'
            font_size: '14sp'
        Slider:
            id: speed_slider
            min: 1
            max: 200
            value: root.speed_kmh
            step: 1
            on_value: root.on_slider_change(self.value)
        Label:
            id: speed_label
            text: '{:.0f} km/h'.format(root.speed_kmh)
            size_hint_x: None
            width: '72dp'
            font_size: '14sp'

    # Preset buttons row
    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: '36dp'
        spacing: '6dp'
        Button:
            text: '步行 5'
            font_size: '13sp'
            on_release: root.set_preset(5)
        Button:
            text: '騎車 20'
            font_size: '13sp'
            on_release: root.set_preset(20)
        Button:
            text: '開車 60'
            font_size: '13sp'
            on_release: root.set_preset(60)
        Button:
            text: '高速 120'
            font_size: '13sp'
            on_release: root.set_preset(120)
""")


class SpeedPanel(BoxLayout):
    """
    Speed control panel: slider (1-200 km/h) + quick-preset buttons.

    Bind `on_speed_change` to receive updates:
        panel.bind(speed_kmh=my_callback)
    """

    speed_kmh = NumericProperty(5.0)

    def on_slider_change(self, value: float):
        self.speed_kmh = float(value)

    def set_preset(self, kmh: int):
        self.speed_kmh = float(kmh)
        self.ids.speed_slider.value = float(kmh)
