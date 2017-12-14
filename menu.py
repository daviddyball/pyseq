from kivy.app import App
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.togglebutton import ToggleButton

__all__ = ['Menu']


class TransportButton(ToggleButton):
    text = StringProperty('Play')

    def on_state(self, obj, state):
        if state == 'down':
            App.get_running_app().start_playback()
            self.text = 'Pause'
        else:
            App.get_running_app().stop_playback()
            self.text = 'Start'


class DisplayWidget(BoxLayout):
    def __init__(self, **kwargs):
        kwargs['orientation'] = 'vertical'
        super(DisplayWidget, self).__init__(**kwargs)
        self.lbl_octave = Label()
        self.lbl_step_range = Label()
        self.lbl_current_step = Label()
        self.top_container = BoxLayout()
        self.top_container.add_widget(self.lbl_octave)
        self.top_container.add_widget(self.lbl_current_step)
        self.add_widget(self.top_container)
        self.add_widget(self.lbl_step_range)


class SequenceSelector(Spinner):
    def __init__(self, *args, **kwargs):
        super(SequenceSelector, self).__init__(*args, **kwargs)
        self.app = App.get_running_app()
        if self.app and hasattr(self.app, 'sequencers'):
            for sequencer_id in range(len(self.app.sequencers)):
                self.values.append('Sequencer {}'.format(sequencer_id))

    def on_text(self, obj, text):
        try:
            text = text.replace('Sequencer ', '')
            self.app.active_sequencer = int(text)
        except ValueError:
            pass


class Menu(BoxLayout):
    orientation = StringProperty('horizontal')

    def update_display_values(self, octave, step_range, current_step_id):
        self.display.lbl_octave.text = 'Octave: {}'.format(octave)
        self.display.lbl_step_range.text = 'Step Range: {}'.format(step_range)
        self.display.lbl_current_step.text = 'Step: {}'.format(current_step_id)

    def __init__(self, *args, **kwargs):
        super(Menu, self).__init__(*args, **kwargs)
        self.size_hint_y = 0.2
        self.display = DisplayWidget()
        self.add_widget(TransportButton())
        self.add_widget(self.display)
        self.add_widget(SequenceSelector())


class TestWidget(App):
    def build(self):
        self.sequencers = [object()]
        self.root = BoxLayout(orientation='vertical')
        self.root.add_widget(Menu())

        from kivy.uix.widget import Widget
        self.root.add_widget(Widget())
        return Menu()


if __name__ == '__main__':
    TestWidget().run()
