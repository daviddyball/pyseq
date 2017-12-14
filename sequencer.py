from midi_engine import midi_engine


__all__ = ['Sequencer']

MAXIMUM_BARS = 7       # Zero indexed so 7 == 8 bars
MAXIMUM_OCTAVES = 4    # 0 - 4 == 5 Octaves (2 == Octave 4)


class Note(object):
    def __init__(self, value=None, is_hold=False):
        self.is_hold = is_hold
        self.value = value

    def __repr__(self):
        return u'<Note value={}, is_hold={}>'.format(self.value, self.is_hold)


class Sequencer(object):
    def __init__(self, id, **kwargs):
        self.id = id
        self.active_step = 0

        bars = kwargs.get('bars', MAXIMUM_BARS)
        self.bars = bars if bars <= MAXIMUM_BARS else MAXIMUM_BARS
        self.beats_per_bar = kwargs.get('beats_per_bar', 4)
        self.beat_subdivision = kwargs.get('steps_per_beat', 4)
        self.steps_per_bar = self.beats_per_bar * self.beat_subdivision
        self.update_step_count()
        self.midi_channel = kwargs.get('midi_channel')

    def update_step_count(self):
        self.step_count = self.bars * self.beats_per_bar * self.beat_subdivision
        if not hasattr(self, 'steps'):
            self.steps = dict(
                [
                    (step_id, Note(None))
                    for step_id in range(self.step_count)
                ]
            )
        else:
            self.steps = {}
            for step_id in range(self.step_count):
                if step_id not in self.steps:
                    self.steps[step_id] = Note(None)

    def get_previous_step(self, step_id=None):
        step_id = step_id or self.active_step
        previous_step_id = step_id - 1 if step_id != 0 else self.step_count - 1
        return self.steps[previous_step_id]

    def get_next_step(self, step_id=None):
        step_id = step_id or self.active_step
        next_step_id = step_id + 1 if step_id != self.step_count else 0
        return self.steps[next_step_id]

    def start_note(self, value):
        if self.midi_channel is not None:
            midi_engine.send_message('NoteOn', self.midi_channel, value)

    def stop_note(self, value):
        if self.midi_channel is not None:
            midi_engine.send_message('NoteOff', self.midi_channel, value)

    def process_step(self, step):
        if step.is_hold:
            return

        previous_step = self.get_previous_step()
        if previous_step.value:
            self.stop_note(previous_step.value)

        if step.value:
            self.start_note(step.value)

    def tick(self, delta):
        self.active_step += 1
        if self.active_step > (self.step_count - 1):
            self.active_step = 0
        self.process_step(self.steps[self.active_step])

    def set_note_for_step(self, step_id, value=None):
        self.steps[step_id].value = value
        self.steps[step_id].is_hold = False

    def clear_note_for_step(self, step_id):
        self.steps[step_id].value = None
        self.steps[step_id].is_hold = False
        current_step = step_id
        while self.get_next_step(current_step).is_hold:
            self.steps[current_step + 1].value = None
            self.steps[current_step + 1].is_hold = False
            current_step = current_step + 1

    def set_note_for_step_range(self, first_step_id, last_step_id, value):
        self.steps[first_step_id].value = value
        self.steps[first_step_id].is_hold = False

        for held_step_id in range(first_step_id + 1, last_step_id + 1):
            if self.steps[held_step_id].value is not None or held_step_id > self.step_count:
                # Bail, we won't override a programmed step
                return
            self.steps[held_step_id].value = value
            self.steps[held_step_id].is_hold = True

        held_step = self.steps[first_step_id]
        if held_step.is_hold or last_step_id > self.step_count:
            return
        for step_id in range(first_step_id + 1, last_step_id + 1):
            self.steps[step_id].value = held_step.value
            self.steps[step_id].is_hold = True

    def set_midi_channel(self, midi_channel):
        self.midi_channel = midi_channel
