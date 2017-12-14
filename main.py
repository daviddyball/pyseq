from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.properties import ListProperty, NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.widget import Widget

from menu import Menu
from sequencer import Sequencer


BLACK_KEY_NOTE_IDS = [1, 3, 6, 8, 10]
NOTE_MAPPING = {
    0: 'C',
    1: 'C#',
    2: 'D',
    3: 'D#',
    4: 'E',
    5: 'F',
    6: 'F#',
    7: 'G',
    8: 'G#',
    9: 'A',
    10: 'A#',
    11: 'B'
}


class StepIndicator(Label):
    color = ListProperty([0.75, 0.75, 0.75, 1])
    height = NumericProperty(10)
    size_hint_y = StringProperty(None)

    def __init__(self, step_id, beat_subdivision, **kwargs):
        if step_id % beat_subdivision == 0:
            kwargs['text'] = str(step_id / beat_subdivision)
        else:
            kwargs['text'] = ''
        super(StepIndicator, self).__init__(**kwargs)


class StepButton(ToggleButton):
    def __init__(self, step_id, note_id, sequencer, **kwargs):
        self.sequencer = sequencer
        self.step_id = step_id
        self.note_id = note_id
        super(StepButton, self).__init__(
            text='{} ({})'.format(step_id, NOTE_MAPPING[self.note_id]),
            group='step_{}'.format(step_id),
            **kwargs
        )


class PianoRollButton(ToggleButton):
    def __init__(self, note_id, **kwargs):
        if note_id in BLACK_KEY_NOTE_IDS:
            texture = 'atlas://data/images/sequencer/pianoroll_key_black'
        else:
            texture = 'atlas://data/images/sequencer/pianoroll_key_white'
        super(PianoRollButton, self).__init__(
            text='{}'.format(NOTE_MAPPING[note_id]),
            color=[1, 0, 1, 1],
            disabled=True,
            background_disabled_normal=texture,
            **kwargs
        )


class PianoRollWidget(BoxLayout):
    def __init__(self, sequencer, **kwargs):
        super(PianoRollWidget, self).__init__(**kwargs)
        self.active_octave = 5
        self.add_widget(Widget(height=10, size_hint_y=None))
        for note_id in reversed(range(12)):
            self.add_widget(PianoRollButton(note_id))


class StepWidget(BoxLayout):
    def __init__(self, sequencer, step_id, **kwargs):
        super(StepWidget, self).__init__(
            orientation='vertical',
            width='25dp',
            **kwargs
        )
        self.step_id = step_id
        self.active_octave = 5
        self.active_step_indicator = StepIndicator(step_id, sequencer.beat_subdivision)
        self.sequencer = sequencer
        self.add_widget(self.active_step_indicator)
        for note_id in reversed(range(12)):
            self.add_widget(StepButton(self.step_id, note_id, self.sequencer))

    def set_active_step_indicator(self):
        self.active_step_indicator.texture = 'atlas://data/images/sequencer/step_indicator_active'

    def clear_active_step_indicator(self):
        self.active_step_indicator.color = 'atlas://data/images/sequencer/step_indicator'


class SequencerView(BoxLayout):
    def __init__(self, **kwargs):
        super(SequencerView, self).__init__(**kwargs)
        self.sequencer = kwargs.pop('sequencer')
        self.right_nav_box = BoxLayout(orientation='vertical', size_hint_x=None, width='25dp')
        self.right_nav_box.add_widget(Button(text='Up'))
        self.right_nav_box.add_widget(Button(text='Dn'))
        self.bottom_nav_box = BoxLayout(orientation='horizontal', size_hint_y=None, height='25dp')
        self.bottom_nav_box.add_widget(Button(text='<'))
        self.bottom_nav_box.add_widget(Button(text='>'))
        self.step_container = BoxLayout(orientation='horizontal')
        for step_id in range(self.sequencer.beats_per_bar * self.sequencer.beat_subdivision):
            self.step_container.add_widget(StepWidget(self.sequencer, step_id))
        self.add_widget(PianoRollWidget(self.sequencer))
        self.add_widget(self.step_container)

    def tick(self, delta):
        self.update_active_step_id()

    def update_active_step_id(self):
        for step in self.children:
            if step.id == self.sequencer.active_step:
                step.set_active_step_indicator()
            else:
                step.clear_active_step_indicator()


class SequencerApp(App):
    active_sequencer = NumericProperty(0)
    sequencers = []
    step_timer = None
    bpm = 120
    steps_per_beat = 4
    tick_interval = 1.0 / (bpm * steps_per_beat)

    def get_active_sequencer(self):
        return self.sequencers[self.active_sequencer]

    def start_playback(self):
        self.step_timer = Clock.schedule_interval(self.tick, self.tick_interval)

    def stop_playback(self):
        if self.step_timer:
            self.step_timer.cancel()
            self.step_timer = None

    def tick(self, delta):
        for sequencer in self.sequencers:
            sequencer.tick(delta)
        sequencer = self.get_active_sequencer()
        first_step = self.current_bar * sequencer.beat_subdivision * sequencer.beats_per_bar
        last_step = first_step + (sequencer.beat_subdivision * sequencer.beats_per_bar)
        self.menu.update_display_values(
            self.current_octave,
            '{} - {}'.format(first_step, last_step),
            self.get_active_sequencer().active_step
        )

    def initialize(self):
        self.current_octave = 0
        self.current_bar = 0
        self.menu = Menu()
        self.active_sequencer = 0
        self.sequencers = [
            Sequencer(id=_id, bars=1, beats_per_bar=4, steps_per_beat=self.steps_per_beat, midi_channel=0)
            for _id in range(8)
        ]

    def build(self):
        self.initialize()
        self.build_gui()

    def build_gui(self):
        self.root = BoxLayout(orientation='vertical', padding='2dp', spacing='2dp')
        self.root.screen_manager = ScreenManager()
        self.root.add_widget(self.menu)
        self.sequencer_view = SequencerView()
        self.root.add_widget(self.sequencer_view)
        return self.root


if __name__ == '__main__':
    SequencerApp().run()
