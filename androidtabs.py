#!python
from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.behaviors import ToggleButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.carousel import Carousel
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.effects.scroll import ScrollEffect
from kivy.graphics import Color, Rectangle
from kivy.properties import ObjectProperty, NumericProperty
from kivy.properties import VariableListProperty, StringProperty
from kivy.properties import AliasProperty, BoundedNumericProperty


Builder.load_string("""
<AndroidTabsLabel>:
    padding: '12dp', 0
    halign: 'center'
    text_normal_color: 1,1,1,.6
    text_active_color: 1

<AndroidTabsHeader>:
    tab_indicator_color: 1,1,1,1
    tab_indicator_height: '2dp'    
""")


class AndroidTabsException(Exception):
    '''The AndroidTabsException class.'''
    pass


class AndroidTabsPanel(Widget):

    label = StringProperty('')
    _tab = ObjectProperty(None)


class Panel(ScrollView, AndroidTabsPanel):

    pass


class AndroidTabsLabel(ToggleButtonBehavior, Label):

    _panel = ObjectProperty(None)
    _androidtabs = ObjectProperty(None)
    _min_space = NumericProperty(0)
    text_normal_color = VariableListProperty([1,1,1,.6])
    text_active_color = VariableListProperty([1])

    def __init__(self, **kwargs):
        self._trigger_update_text = Clock.schedule_once(self._update_text, 0)
        super(AndroidTabsLabel, self).__init__(**kwargs)
        self.allow_no_selection = False
        self.group = 'tabs'
        self.size_hint = (None, 1)
        self.color = self.text_normal_color
        self.bind(
            x=self._update_tab_indicator,
            width=self._update_tab_indicator,
            )

    def on__panel(self, widget, panel):

        if panel:
            panel.bind(label=self._trigger_update_text)
        else:
            panel.unbind(label=self._trigger_update_text)

    def _update_text(self, *args):

        if self._panel:

            self.text = self._panel.label

    def on_touch_down(self, touch):
        # only allow selecting the tab if not already selected
        if self.state is 'down':
            return
        super(AndroidTabsLabel, self).on_touch_down(touch)

    def on_release(self, *args):

        if self.state == 'down':

            self._androidtabs._carousel.load_slide(self._panel)

    def on_texture(self, widget, texture):

        if texture:

            self.width = texture.width
            self._min_space = self.width

    def on_state(self, widget, state):

        if state == 'down':
            self.color = self.text_active_color
        else:
            self.color = self.text_normal_color

    def _update_tab_indicator(self, *args):

        if self is self._androidtabs._carousel.current_slide._tab:

            self._androidtabs._header._update_tab_indicator(self.x, self.width)


class AndroidTabsHeaderContainer(FloatLayout):

    def __init__(self, **kwargs):
        super(AndroidTabsHeaderContainer, self).__init__(**kwargs)
        

class AndroidTabsHeader(BoxLayout):

    tab_indicator_height = NumericProperty('2dp')
    tab_indicator_color = VariableListProperty([1])

    def __init__(self, **kwargs):

        self._trigger_update_tabs = Clock.schedule_once(self._update_tabs, 0)
        super(AndroidTabsHeader, self).__init__(**kwargs)
        self._scrollview = ScrollView(
            size_hint = (1, 1),
            do_scroll_y = False,
            bar_color = (0, 0, 0, 0),
            effect_cls = ScrollEffect,
            )
        self._layout = GridLayout(
            rows=1,
            size_hint=(None, 1),
            )
        self._layout.bind(
            minimum_width=self._layout.setter('width'),
            width=self._trigger_update_tabs,
            )
        self._scrollview.add_widget(self._layout)
        self.add_widget(self._scrollview)

        with self._layout.canvas.after:
            r, g, b, a = self.tab_indicator_color
            Color(r, g, b, a)
            self._tab_indicator = Rectangle(
                pos=(0, 0),
                size=(0, self.tab_indicator_height)
                )

        self.bind(width=self._trigger_update_tabs)

    def _update_tab_indicator(self, x, w):

        self._tab_indicator.pos = (x, 0)
        self._tab_indicator.size = (w, self._tab_indicator.size[1])

    def _update_tabs(self, *args, **kwargs):

        header, width, tabs = self, self.width, self._layout.children
        tabs_widths = [t._min_space for t in tabs if t._min_space]
        tabs_space = float(sum(tabs_widths))
        if not tabs_space:
            return
        ratio = width / tabs_space
        use_ratio = True in (width / len(tabs) < w for w in tabs_widths)

        for t in tabs:

            t.width = t._min_space if tabs_space > width \
                        else t._min_space * ratio if use_ratio is True \
                        else width / len(tabs)


class AndroidTabs(BoxLayout):

    _carousel = ObjectProperty(None)
    _header = ObjectProperty(None)
    _target_slide = ObjectProperty(None)

    def get_last_scroll_x(self, *args):

        return self._header._scrollview.scroll_x

    _last_scroll_x = AliasProperty(
        get_last_scroll_x, None,
        bind=('_target_slide', ),
        cache=True,
        )

    default_tab = NumericProperty(0)
    anim_duration = NumericProperty(0.20)
    anim_threshold = BoundedNumericProperty(
        0.8, min=0.0, max=1.0,
        errorhandler=lambda x: 0.0 if x < 0.0 else 1.0
        )

    header_height = NumericProperty('48dp')

    def __init__(self, **kwargs):

        self.padding = (0, self.header_height, 0, 0)
        super(AndroidTabs, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self._threshold_data = ()
        self._carousel = Carousel(anim_move_duration=self.anim_duration)
        self._carousel.bind(
            index=self.on_index,
            _offset=self.android_animation,
            )
        self._header_container = AndroidTabsHeaderContainer(
            size_hint=(1, None),
            )
        self._header = AndroidTabsHeader(
            size_hint=(1, None),
            height=self.header_height,
            )
        self._header_container.add_widget(self._header)
        super(AndroidTabs, self).add_widget(self._carousel)
        super(AndroidTabs, self).add_widget(self._header_container)
        if self._carousel.slides:
            self._carousel.index = self.default_tab

    def on_size(self, widget, size):

        if self._header:

            self._header.y = self.top - self.header_height

    def on_index(self, carousel, index):

        current_tab = carousel.current_slide._tab
        if current_tab.state == 'normal':
            current_tab._do_press()
        self._threshold_data = ()
        self._header._update_tab_indicator(current_tab.x, current_tab.width)

    def add_widget(self, widget):

        if not issubclass(widget.__class__, AndroidTabsPanel):

            raise AndroidTabsException(
                'AndroidTabs accept only subclass of AndroidTabsPanel'
                )

        new_tab = AndroidTabsLabel(
            _panel=widget,
            _androidtabs=self,
            )

        widget._tab = new_tab
        self._header._layout.add_widget(new_tab)
        self._carousel.add_widget(widget)

    def remove_widget(self, widget):

        if not issubclass(widget.__class__, AndroidTabsPanel):

            raise AndroidTabsException(
                'AndroidTabs can remove only subclass of AndroidTabsPanel'
                )

        if widget.parent.parent is self._carousel:

            self._carousel.remove_widget(widget)
            self._header._layout.remove_widget(widget._tab)

    def auto_scroll(self, target, step):

        t = target
        bound_left = self._header.width / 2
        bound_right = self._header._layout.width - bound_left
        dt = t.center_x - (self._header.width / 2)
        sx, sy = self._header._scrollview.convert_distance_to_scroll(dt, 0)

        lsx = self._last_scroll_x
        dst = abs(lsx - sx)
        scroll_is_late = lsx < sx

        if scroll_is_late and t.center_x > bound_left:

            x = lsx + (dst * step)
            self._header._scrollview.scroll_x = x if x < 1.0 else 1.0

        elif not scroll_is_late and t.center_x < bound_right:

            x = lsx - (dst * step)
            self._header._scrollview.scroll_x = x if x > 0.0 else 0.0

    def android_animation(self, carousel, offset):

        if offset != 0 and abs(offset) < self.width:

            forward = offset < 0
            offset = abs(offset)
            step = offset / float(carousel.width)
            moving = abs(offset - carousel.width)

            skip_slide = carousel.slides[carousel._skip_slide] \
                        if carousel._skip_slide is not None else False
            next_slide = carousel.next_slide \
                        if forward else carousel.previous_slide
            self._target_slide = skip_slide if skip_slide \
                        else next_slide if next_slide is not None \
                        else carousel.current_slide

            a = carousel.current_slide._tab
            b = self._target_slide._tab

            if self._target_slide is self._carousel.current_slide:
                return

            # Header automatic scroll animation
            self.auto_scroll(b, step)

            if step <= self.anim_threshold:

                if forward:
                    gap = abs((a.x + a.width) - (b.x + b.width))
                    w_step = a.width + (gap * step)
                    x_step = a.x

                else:
                    gap = abs((a.x - b.x)) * step
                    x_step = a.x - gap
                    w_step = a.width + gap

            else:

                if not self._threshold_data:
                    self._threshold_data = (
                        self._header._tab_indicator.size[0],
                        self._header._tab_indicator.pos[0],
                        moving,
                        )

                bar_width_peak, bar_pos_peak, breakpoint = self._threshold_data

                step = 1.0 - (moving / breakpoint)
                gap_w = bar_width_peak - b.width
                w_step = bar_width_peak - (gap_w * step)

                if forward:
                    x_step = a.x + abs((a.x - b.x)) * step

                else:
                    gap_x = bar_pos_peak - b.x
                    x_step = bar_pos_peak - (gap_x * step)

            self._header._update_tab_indicator(x_step, w_step)

if __name__ == '__main__':

    class MainApp(App):

        def build(self):

            android_tabs = AndroidTabs()

            for n in range(1, 6):

                panel = Panel(label='Tab %s' % n)
                panel.add_widget(Button(text='%s' % n))
                android_tabs.add_widget(panel)

            return android_tabs

    MainApp().run()
