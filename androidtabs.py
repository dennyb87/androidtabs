#!python

"""
AndroidTabs
===========
AndroidTabs try to reproduce the behaviours of Android Tabs.
It allow you to create your own custom tabbed panel
with an animated tab indicator in a easy way.
Just create your tabs that must inherit from AndroidTabsBase
and add them to an AndroidTabs instance.

class MyTab(BoxLayout, AndroidTabsBase):

    pass

android_tabs = AndroidTabs()

for n in range(5):

    tab = MyTab(text='Tab %s' % n)
    tab.add_widget(Button(text='Button %s' % n))
    android_tabs.add_widget(tab)
"""

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
from kivy.graphics import Color, Rectangle
from kivy.properties import (
    ObjectProperty,
    NumericProperty,
    VariableListProperty,
    StringProperty,
    AliasProperty,
    BoundedNumericProperty,
    ReferenceListProperty
)


class AndroidTabsException(Exception):
    '''The AndroidTabsException class'''
    pass


class AndroidTabsLabel(ToggleButtonBehavior, Label):
    '''
    AndroidTabsLabel it represent the label of each tab.
    '''

    text_color_normal = VariableListProperty([1, 1, 1, .6])
    '''
    Text color of the label when it is not selected.
    '''

    text_color_active = VariableListProperty([1])
    '''
    Text color of the label when it is selected.
    '''

    _tab = ObjectProperty(None)
    _root = ObjectProperty(None)

    def __init__(self, **kwargs):

        super(AndroidTabsLabel, self).__init__(**kwargs)
        self._min_space = 0

    def on_touch_down(self, touch):
        # only allow selecting the tab if not already selected
        if self.state is 'down':
            return
        super(AndroidTabsLabel, self).on_touch_down(touch)

    def on_release(self):
        # if the label is selected load the relative tab from carousel
        if self.state == 'down':
            self._root._carousel.load_slide(self._tab)

    def on_texture(self, widget, texture):
        # just save the minimum width of the label based of the content
        if texture:
            self.width = texture.width
            self._min_space = self.width

    def _update_tab_indicator(self):
        # update the position and size of the board of the indicator
        # when the label changes size or position
        if self is self._root._carousel.current_slide._tab_label:
            self._root._update_tab_indicator(self.x, self.width)


class AndroidTabsBase(Widget):

    '''
    AndroidTabsBase allow you to create a tab.
    You must create a new class that inherits
    from AndroidTabsBase.
    In this way you have total control over the
    views of your tabbed panel.
    '''

    text = StringProperty('')
    '''
    It will be the label text of the tab.
    '''

    _tab_label = ObjectProperty(None)
    '''
    It is the label object reference of the tab.
    '''

    def __init__(self, **kwargs):

        self._tab_label = AndroidTabsLabel()
        self._tab_label._tab = self
        super(AndroidTabsBase, self).__init__(**kwargs)

    def on_text(self, widget, text):
        # set the label text
        self._tab_label.text = self.text


class AndroidTabsMain(BoxLayout):
    '''
    AndroidTabsMain is just a boxlayout that contain
    the carousel. It allows you to have control over the carousel.
    '''


class AndroidTabsHeader(FloatLayout):
    '''
    AndroidTabsHeader contain the tab bar.
    It only serves to bring the tab bar widget above all other widgets
    just in case you want to add a shadow.
    '''
    pass


class AndroidTabsBar(BoxLayout):
    '''
    AndroidTabsBar is just a boxlayout that contain
    the scrollview for the tabs.
    It is also responsible to resize the tab label when it needed.
    '''

    def __init__(self, **kwargs):

        self._trigger_update_tab_labels_width = Clock.schedule_once(
            self._update_tab_labels_width, 0)
        super(AndroidTabsBar, self).__init__(**kwargs)

    def _update_tab_labels_width(self, *args, **kwargs):
        # update width of the labels when it is needed
        width, tabs = self.width, self._layout.children
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
    '''
    The AndroidTabs class.
    You can use it to create your own custom tabbed panel.
    '''

    default_tab = NumericProperty(0)
    '''
    Index of the default tab. Default to 0.
    '''

    tab_indicator_height = NumericProperty('2dp')
    '''
    Height of the tab indicator.
    '''

    tab_indicator_color = VariableListProperty([1])
    '''
    Color of the tab indicator.
    '''

    anim_duration = NumericProperty(0.2)
    '''
    Duration of the animation. Default to 0.2.
    '''

    anim_threshold = BoundedNumericProperty(
        0.8, min=0.0, max=1.0,
        errorhandler=lambda x: 0.0 if x < 0.0 else 1.0)
    '''
    Animation threshold allow you to change the animation effect.
    Default to 0.8.
    '''

    _target_tab = ObjectProperty(None)
    '''
    Is the carousel reference of the next tab / slide.
    When you go from "Tab A" to "Tab B", "Tab B" will be the
    target tab / slide of the carousel.
    '''

    def get_last_scroll_x(self):

        return self._tab_bar._scrollview.scroll_x

    _last_scroll_x = AliasProperty(
        get_last_scroll_x, None,
        bind=('_target_tab', ),
        cache=True)
    '''
    It keep track of the last scroll_x value of the tab bar.
    '''

    def __init__(self, **kwargs):
        super(AndroidTabs, self).__init__(**kwargs)
        self._threshold_data = ()
        self._tab_indicator_builder()

    def _tab_indicator_builder(self):
        # build tab indicator
        self._tab_bar._layout.canvas.after.clear()
        with self._tab_bar._layout.canvas.after:
            r, g, b, a = self.tab_indicator_color
            Color(r, g, b, a)
            self._tab_indicator = Rectangle(
                pos=(0, 0),
                size=(0, self.tab_indicator_height))

    def _update_tab_indicator(self, x, w):
        # update position and size of the indicator
        self._tab_indicator.pos = (x, 0)
        self._tab_indicator.size = (w, self.tab_indicator_height)

    def on_index(self, carousel, index):
        # when the index of the carousel change, the changes are applied.
        self._threshold_data = ()
        current_tab_label = carousel.current_slide._tab_label
        if current_tab_label.state == 'normal':
            current_tab_label._do_press()
        self._update_tab_indicator(current_tab_label.x, current_tab_label.width)

    def add_widget(self, widget):
        # You can add only subclass of AndroidTabsBase.
        if len(self.children) >= 2:

            if not issubclass(widget.__class__, AndroidTabsBase):
                raise AndroidTabsException(
                    'AndroidTabs accept only subclass of AndroidTabsBase')

            widget._tab_label._root = self
            self._tab_bar._layout.add_widget(widget._tab_label)
            self._carousel.add_widget(widget)
            return

        return super(AndroidTabs, self).add_widget(widget)

    def remove_widget(self, widget):
        # You can remove only subclass of AndroidTabsBase.
        if not issubclass(widget.__class__, AndroidTabsBase):

            raise AndroidTabsException(
                'AndroidTabs can remove only subclass of AndroidTabBase')

        if widget.parent.parent == self._carousel:

            # remove tab label from the tab bar
            self._tab_bar._layout.remove_widget(widget._tab_label)

            # remove tab from carousel
            self._carousel.remove_widget(widget)

    def tab_bar_autoscroll(self, target, step):
        # automatic scroll animation of the tab bar.
        t = target
        bound_left = self._tab_bar.width / 2
        bound_right = self._tab_bar._layout.width - bound_left
        dt = t.center_x - (self._tab_bar.width / 2)
        sx, sy = self._tab_bar._scrollview.convert_distance_to_scroll(dt, 0)

        # last scroll x of the tab bar
        lsx = self._last_scroll_x

        # distance to run
        dst = abs(lsx - sx)

        # determine scroll direction
        scroll_is_late = lsx < sx

        if scroll_is_late and t.center_x > bound_left:
            x = lsx + (dst * step)
            self._tab_bar._scrollview.scroll_x = x if x < 1.0 else 1.0

        elif not scroll_is_late and t.center_x < bound_right:
            x = lsx - (dst * step)
            self._tab_bar._scrollview.scroll_x = x if x > 0.0 else 0.0

    def android_animation(self, carousel, offset):
        # try to reproduce the android animation effect.
        if offset != 0 and abs(offset) < self.width:
            forward = offset < 0
            offset = abs(offset)
            step = offset / float(carousel.width)
            moving = abs(offset - carousel.width)

            if not moving:
                return

            skip_slide = carousel.slides[carousel._skip_slide] \
                        if carousel._skip_slide is not None else False
            next_slide = carousel.next_slide \
                        if forward else carousel.previous_slide
            self._target_tab = skip_slide if skip_slide \
                        else next_slide if next_slide is not None \
                        else carousel.current_slide

            a = carousel.current_slide._tab_label
            b = self._target_tab._tab_label

            if self._target_tab is self._carousel.current_slide:
                return

            # tab bar automatic scroll animation
            self.tab_bar_autoscroll(b, step)

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

                # keep track of indicator data in the threshold
                # to calculate the distance which is left to run
                if not self._threshold_data:
                    self._threshold_data = (
                        self._tab_indicator.size[0],
                        self._tab_indicator.pos[0],
                        moving)

                ind_width, ind_pos, breakpoint = self._threshold_data

                step = 1.0 - (moving / breakpoint)
                gap_w = ind_width - b.width
                w_step = ind_width - (gap_w * step)

                if forward:
                    x_step = a.x + abs((a.x - b.x)) * step

                else:
                    gap_x = ind_pos - b.x
                    x_step = ind_pos - (gap_x * step)

            # updates the indicator at the end of each step
            self._update_tab_indicator(x_step, w_step)


Builder.load_string('''
#:import ScrollEffect kivy.effects.scroll.ScrollEffect
<AndroidTabsLabel>:
    allow_no_selection: False
    group: 'tabs'
    size_hint: None, 1
    halign: 'center'
    padding: '12dp', 0
    text_color_normal: 1, 1, 1, .6
    text_color_active: 1, 1, 1, 1
    color: self.text_color_active if self.state is 'down' \
                                else self.text_color_normal
    on_x: self._update_tab_indicator()
    on_width: self._update_tab_indicator()

<AndroidTabsBar>:
    _scrollview: scrollview
    _layout: gridlayout
    on_width: self._trigger_update_tab_labels_width()
    size_hint: 1, None
    height: '48dp'

    ScrollView:
        id: scrollview
        size_hint: 1, 1
        do_scroll_y: False
        bar_color: 0, 0, 0, 0
        effect_cls: ScrollEffect

        GridLayout:
            id: gridlayout
            rows: 1
            size_hint: None, 1
            width: self.minimum_width
            on_width: root._trigger_update_tab_labels_width()

<AndroidTabsHeader>:
    size_hint: 1, None

<AndroidTabs>:
    _tab_bar: tab_bar
    _carousel: carousel
    orientation: 'vertical'
    padding: 0, tab_bar.height, 0, 0

    AndroidTabsMain:

        Carousel:
            id: carousel
            anim_move_duration: root.anim_duration
            on_index: root.on_index(*args)
            on__offset: root.android_animation(*args)
            on_slides: root.on_index(self, root.default_tab)

    AndroidTabsHeader:

        AndroidTabsBar:
            id: tab_bar
            y: root.top - self.height
''')

kvdemo = '''
#:import hex_to_kvcolor kivy.utils.get_color_from_hex

<AndroidTabsBar>:
    height: '68dp'
    canvas.before:
        Color:
            rgba: hex_to_kvcolor('#03A9F4')
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: 0,0,0,.3
        Rectangle:
            pos: self.pos[0], self.pos[1] - 1
            size: self.size[0], 1
        Color:
            rgba: 0,0,0,.2
        Rectangle:
            pos: self.pos[0], self.pos[1] - 2
            size: self.size[0], 1
        Color:
            rgba: 0,0,0,.05
        Rectangle:
            pos: self.pos[0], self.pos[1] - 3
            size: self.size[0], 1

<AndroidTabs>:
    MyTab:
        text: 'TAB N 1'

<MyTab>:
    text: self.text
    canvas:
        Color:
            rgba: 1,1,1,1
        Rectangle:
            pos: self.pos
            size: self.size
    Label:
        text: root.text
        color: 0,0,0,1
'''


if __name__ == '__main__':

    class MyTab(BoxLayout, AndroidTabsBase):

        pass

    class MainApp(App):

        def build(self):

            Builder.load_string(kvdemo)
            android_tabs = AndroidTabs()

            for n in range(2, 6):

                tab = MyTab(text='TAB N %s' % n)
                android_tabs.add_widget(tab)

            return android_tabs

    MainApp().run()
