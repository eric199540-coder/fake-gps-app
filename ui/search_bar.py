from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty
from kivy.lang import Builder

Builder.load_string("""
<SearchBar>:
    orientation: 'horizontal'
    size_hint_y: None
    height: '40dp'
    spacing: '4dp'
    padding: [4, 2, 4, 2]

    TextInput:
        id: search_input
        hint_text: '輸入地址或「緯度,經度」'
        multiline: False
        font_size: '14sp'
        on_text_validate: root.do_search()

    Button:
        text: '搜尋'
        size_hint_x: None
        width: '64dp'
        font_size: '14sp'
        on_release: root.do_search()
""")


class SearchBar(BoxLayout):
    """
    Search bar that emits on_search_result(lat, lng) or on_search_error(msg).

    Usage:
        bar = SearchBar()
        bar.bind(on_search_result=my_handler)
    """

    on_search_result = ObjectProperty(None, allownone=True)
    on_search_error = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        self.register_event_type('on_search_result')
        self.register_event_type('on_search_error')
        super().__init__(**kwargs)

    def do_search(self):
        from logic.geocoder import geocode
        query = self.ids.search_input.text.strip()
        if not query:
            return
        geocode(
            query,
            on_success=lambda lat, lng: self.dispatch('on_search_result', lat, lng),
            on_error=lambda msg: self.dispatch('on_search_error', msg),
        )

    # Default event handlers
    def on_search_result(self, lat, lng):
        pass

    def on_search_error(self, msg):
        pass
