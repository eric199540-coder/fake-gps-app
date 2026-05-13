from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from typing import Callable, Optional


class CoordEditPopup(Popup):
    """
    Modal dialog for manually editing latitude and longitude.

    Usage:
        popup = CoordEditPopup(
            lat=25.033,
            lng=121.565,
            on_confirm=lambda lat, lng: ...,
        )
        popup.open()
    """

    def __init__(
        self,
        lat: float,
        lng: float,
        on_confirm: Callable[[float, float], None],
        **kwargs,
    ):
        kwargs.setdefault('title', '編輯座標')
        kwargs.setdefault('size_hint', (0.85, None))
        kwargs.setdefault('height', '220dp')
        kwargs.setdefault('auto_dismiss', True)
        super().__init__(**kwargs)

        self._on_confirm = on_confirm
        self._error_label: Optional[Label] = None

        # Build content
        root = BoxLayout(orientation='vertical', spacing='8dp', padding='12dp')

        grid = GridLayout(cols=2, spacing='6dp', size_hint_y=None, height='80dp')
        grid.add_widget(Label(text='緯度 (lat):', halign='right', valign='middle'))
        self._lat_input = TextInput(
            text=str(lat), multiline=False, input_filter='float'
        )
        grid.add_widget(self._lat_input)

        grid.add_widget(Label(text='經度 (lng):', halign='right', valign='middle'))
        self._lng_input = TextInput(
            text=str(lng), multiline=False, input_filter='float'
        )
        grid.add_widget(self._lng_input)
        root.add_widget(grid)

        # Error label (hidden until needed)
        self._error_label = Label(
            text='', color=(1, 0.3, 0.3, 1), size_hint_y=None, height='20dp'
        )
        root.add_widget(self._error_label)

        # Buttons
        btn_row = BoxLayout(
            orientation='horizontal', spacing='8dp', size_hint_y=None, height='40dp'
        )
        cancel_btn = Button(text='取消')
        cancel_btn.bind(on_release=lambda _: self.dismiss())
        confirm_btn = Button(text='確認', background_color=(0.2, 0.7, 0.3, 1))
        confirm_btn.bind(on_release=self._on_confirm_pressed)
        btn_row.add_widget(cancel_btn)
        btn_row.add_widget(confirm_btn)
        root.add_widget(btn_row)

        self.content = root

    def _on_confirm_pressed(self, _):
        try:
            lat = float(self._lat_input.text)
            lng = float(self._lng_input.text)
        except ValueError:
            self._error_label.text = '請輸入有效的數字'
            return

        if not (-90 <= lat <= 90):
            self._error_label.text = '緯度範圍：-90 ～ 90'
            return
        if not (-180 <= lng <= 180):
            self._error_label.text = '經度範圍：-180 ～ 180'
            return

        self.dismiss()
        self._on_confirm(lat, lng)
