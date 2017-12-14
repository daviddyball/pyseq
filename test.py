from kivy.app import App
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.properties import NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.togglebutton import ToggleButton

from sequencer import MAXIMUM_OCTAVES, Sequencer


class StepWidget(BoxLayout):
    def __init__(self, sequencer_view, step_id, **kwargs):
        self.step_id = step_id
        self.app = App.get_running_app()
        super(StepWidget, self).__init__(**kwargs)


class TransportButton(ToggleButton):
    def __init__(self, *args, **kwargs):
        super(TransportButton, self).__init__(*args, **kwargs)
        self.app = App.get_running_app()

    def on_state(self, button, state):
        if state == 'down':
            self.app.start_playback()
            self.text = 'Pause'
        else:
            self.app.stop_playback()
            self.text = 'Start'


class Menu(BoxLayout):
    def update_display(self, octave, current_bar, total_bars, active_step, steps_per_beat):
        self.ids['lbl_octave'].text = 'Octave: {}'.format(octave)
        self.ids['lbl_bar'].text = 'Bar: {}/{}'.format(current_bar, total_bars)
        self.ids['lbl_current_beat'].text = str(int(active_step / steps_per_beat))


class SequencerView(BoxLayout):
    def __init__(self, *args, **kwargs):
        super(SequencerView, self).__init__(*args, **kwargs)
        self.app = App.get_running_app()
        for step_id in range(self.app.active_sequencer.steps_per_bar):
            self.step_container.add_widget(StepWidget(self.app, step_id))

    def _reset_step_view(self):
        for step_widget in self.step_container.children:
            for step in step_widget.children:
                step.background_color = [1, 1, 1, 1]
        self.update_ui(None)

    def _update_step_view(self, delta):
        current_octave_start = self.app.current_octave * 12
        current_octave_end = current_octave_start + 12
        current_note_range = range(current_octave_start, current_octave_end)
        current_bar_start = self.app.current_bar * self.app.active_sequencer.steps_per_bar
        current_bar_end = current_bar_start + self.app.active_sequencer.steps_per_bar
        current_step_range = range(current_bar_start, current_bar_end)
        for step_widget in self.step_container.children:
            sequencer_step_note_id = self.app.active_sequencer.steps[step_widget.step_id].value

            if step_widget.step_id != self.app.active_sequencer.active_step:
                color = [1, 1, 1, 1]
            else:
                color = [.5, .5, .5, 1]

            for step_button in step_widget.children:
                computed_button_note_id = (self.app.current_octave * 12) + step_button.note_offset_id
                step_button.background_color = color
                step_button.text = '({})'.format(computed_button_note_id)
                step_button.state = 'normal'
                if sequencer_step_note_id in current_note_range:
                    if computed_button_note_id == sequencer_step_note_id:
                        if step_widget.step_id in current_step_range:
                            step_button.state = 'down'

    def _update_menu(self, delta):
        self.ids['menu'].update_display(
            self.app.current_octave,
            self.app.current_bar,
            self.app.active_sequencer.bars,
            self.app.active_sequencer.active_step,
            self.app.active_sequencer.beat_subdivision
        )

    def _update_navigation(self, delta):
        self.btn_octave_up.disabled = self.app.current_octave == MAXIMUM_OCTAVES
        self.btn_octave_down.disabled = self.app.current_octave == 0
        self.btn_bar_next.disabled = self.app.current_bar == self.app.active_sequencer.bars
        self.btn_bar_previous.disabled = self.app.current_bar == 0

    def update_ui(self, delta):
        self.app.ui_updating = True
        self._update_step_view(delta)
        self._update_navigation(delta)
        self._update_menu(delta)
        self.app.ui_updating = False


class TestApp(App):
    sequencers = []
    step_timer = None
    bpm = NumericProperty(120)

    def get_tick_interval(self):
        return 60.0 / (self.bpm * self.active_sequencer.beat_subdivision)

    def octave_up(self, widget, state):
        self.debug_hold = True
        if state == 'normal':
            return

        if self.current_octave < MAXIMUM_OCTAVES:
            self.current_octave += 1
        self.sequencer_view.update_ui(None)

    def octave_down(self, widget, state):
        if state == 'normal':
            return

        if self.current_octave > 0:
            self.current_octave -= 1
        self.sequencer_view.update_ui(None)

    def previous_bar(self, widget, state):
        if state == 'normal':
            return
        if self.current_bar > 0:
            self.current_bar -= 1
        self.sequencer_view.update_ui(None)

    def next_bar(self, widget, state):
        if state == 'normal':
            return

        if self.current_bar < self.active_sequencer.bars:
            self.current_bar += 1
        self.sequencer_view.update_ui(None)

    def sequence_step(self, widget, state):
        if self.ui_updating:
            return

        if state == 'normal':
            value = None
        else:
            value = (self.current_octave * 12) + widget.note_offset_id
        Logger.info(
            'Scheduling Sequencer #{} to Play Note {} on Step {}'.format(
                self.active_sequencer.id, value, widget.parent.step_id
            )
        )
        self.active_sequencer.set_note_for_step(widget.parent.step_id, value)

    def start_playback(self):
        self.active_sequencer.active_step = 0
        self.step_timer = Clock.schedule_interval(self.tick, self.get_tick_interval())
        Logger.info('Playback Started')

    def stop_playback(self):
        if self.step_timer:
            self.step_timer.cancel()
            self.step_timer = None
        self.sequencer_view._reset_step_view()
        Logger.info('Playback Stopped')

    def switch_sequencer(self, sequencer_id):
        sequencer_id = int(sequencer_id.lstrip('Sequencer #'))
        Logger.info('Switching to Sequencer #{}'.format(sequencer_id))

    def tick(self, delta):
        for sequencer in self.sequencers:
            sequencer.tick(delta)
        self.sequencer_view.update_ui(delta)

    def initialize_app_state(self):
        self.ui_updating = False
        self.current_bar = 0
        self.current_octave = 2

    def build(self):
        self.initialize_app_state()
        self.sequencers = [
            Sequencer(id=_id, bars=1, beats_per_bar=4, steps_per_beat=4, midi_channel=0)
            for _id in range(8)
        ]
        self.active_sequencer = self.sequencers[0]
        self.sequencer_view = SequencerView()
        self.sequencer_view.menu.sequencer_spinner.values = [
            'Sequencer #{}'.format(sequencer_id)
            for sequencer_id in range(len(self.sequencers))
        ]
        self.sequencer_view.update_ui(None)
        return self.sequencer_view


if __name__ == '__main__':
    TestApp().run()
