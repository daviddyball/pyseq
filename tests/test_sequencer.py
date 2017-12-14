import mock

from unittest import TestCase

from sequencer import Sequencer, Note


class TestSequencer(TestCase):
    @mock.patch('sequencer.Sequencer.get_previous_step')
    @mock.patch('midi_engine.MidiEngine.send_message')
    def test_process_step_only_starts_current_note_when_previous_note_is_empty(self, mock_send_message, mock_get_previous_step):
        mock_get_previous_step.return_value = Note(None, is_hold=False)
        sequencer = Sequencer(0, 1, 4, 4)
        sequencer.set_midi_channel(0)
        sequencer.process_step(Note(1, is_hold=False))
        self.assertEquals(mock_send_message.call_count, 1)
        self.assertEquals(mock_send_message.call_args[0], ('NoteOn', 0, 1))

    @mock.patch('sequencer.Sequencer.get_previous_step')
    @mock.patch('midi_engine.MidiEngine.send_message')
    def test_process_step_stops_previous_note_when_previous_note_is_not_empty(self, mock_send_message, mock_get_previous_step):
        mock_get_previous_step.return_value = Note(99, is_hold=False)
        sequencer = Sequencer(0, 1, 4, 4)
        sequencer.set_midi_channel(0)
        sequencer.process_step(Note(1, is_hold=False))
        self.assertEquals(mock_send_message.call_count, 2)
        self.assertEquals(mock_send_message.call_args_list[0][0], ('NoteOff', 0, 99))
        self.assertEquals(mock_send_message.call_args_list[1][0], ('NoteOn', 0, 1))

    @mock.patch('sequencer.Sequencer.get_previous_step')
    @mock.patch('midi_engine.MidiEngine.send_message')
    def test_process_step_stops_previous_note_when_previous_note_is_a_hold_note_and_current_note_is_not_empty(self, mock_send_message, mock_get_previous_step):
        mock_get_previous_step.return_value = Note(99, is_hold=True)
        sequencer = Sequencer(0, 1, 4, 4)
        sequencer.set_midi_channel(0)
        sequencer.process_step(Note(1, is_hold=False))
        self.assertEquals(mock_send_message.call_count, 2)
        self.assertEquals(mock_send_message.call_args_list[0][0], ('NoteOff', 0, 99))
        self.assertEquals(mock_send_message.call_args_list[1][0], ('NoteOn', 0, 1))

    @mock.patch('sequencer.Sequencer.get_previous_step')
    @mock.patch('midi_engine.MidiEngine.send_message')
    def test_process_steps_stops_previous_note_when_current_note_is_empty(self, mock_send_message, mock_get_previous_step):
        mock_get_previous_step.return_value = Note(99, is_hold=False)
        sequencer = Sequencer(0, 1, 4, 4)
        sequencer.set_midi_channel(0)
        sequencer.process_step(Note(None, is_hold=False))
        self.assertEquals(mock_send_message.call_count, 1)
        self.assertEquals(mock_send_message.call_args_list[0][0], ('NoteOff', 0, 99))

    @mock.patch('sequencer.Sequencer.get_previous_step')
    @mock.patch('midi_engine.MidiEngine.send_message')
    def test_process_steps_stops_previous_note_when_previous_note_is_hold_and_current_note_is_empty(self, mock_send_message, mock_get_previous_step):
        mock_get_previous_step.return_value = Note(99, is_hold=True)
        sequencer = Sequencer(0, 1, 4, 4)
        sequencer.set_midi_channel(0)
        sequencer.process_step(Note(None, is_hold=False))
        self.assertEquals(mock_send_message.call_count, 1)
        self.assertEquals(mock_send_message.call_args_list[0][0], ('NoteOff', 0, 99))

    def test_init_calculates_step_count_correctly(self):
        sequencer = Sequencer(0, 1, 4, 4)
        self.assertEquals(sequencer.bars, 1)
        self.assertEquals(sequencer.beats_per_bar, 4)
        self.assertEquals(sequencer.step_subdivision, 4)
        self.assertEquals(sequencer.step_count, 16)
        self.assertEquals(len(sequencer.steps.keys()), 16)

        sequencer = Sequencer(0, 4, 4, 4)
        self.assertEquals(sequencer.bars, 4)
        self.assertEquals(sequencer.beats_per_bar, 4)
        self.assertEquals(sequencer.step_subdivision, 4)
        self.assertEquals(sequencer.step_count, 64)
        self.assertEquals(len(sequencer.steps.keys()), 64)

    def test_set_note_for_step_sets_value_correctly(self):
        sequencer = Sequencer(0, 1, 4, 4)
        sequencer.set_note_for_step(1, 127)
        self.assertEquals(sequencer.steps[1].value, 127)
        self.assertFalse(sequencer.steps[1].is_hold)

    def test_clear_note_for_step_sets_value_correctly(self):
        sequencer = Sequencer(0, 1, 4, 4)
        sequencer.clear_note_for_step(8)
        self.assertEquals(sequencer.steps[8].value, None)
        self.assertFalse(sequencer.steps[8].is_hold)

    def test_set_note_for_step_range_sets_value_and_hold_state_correctly_on_all_steps(self):
        sequencer = Sequencer(0, 1, 4, 4)
        sequencer.set_note_for_step_range(0, 3, 12)
        self.assertEquals(sequencer.steps[0].value, 12)
        self.assertFalse(sequencer.steps[0].is_hold)
        self.assertEquals(sequencer.steps[1].value, 12)
        self.assertTrue(sequencer.steps[1].is_hold)
        self.assertEquals(sequencer.steps[2].value, 12)
        self.assertTrue(sequencer.steps[2].is_hold)
        self.assertEquals(sequencer.steps[3].value, 12)
        self.assertTrue(sequencer.steps[3].is_hold)

    def test_set_note_for_step_range_wont_override_a_step_that_is_already_set(self):
        sequencer = Sequencer(0, 1, 4, 4)
        sequencer.set_note_for_step(2, 12)
        sequencer.set_note_for_step_range(0, 3, 99)
        self.assertEquals(sequencer.steps[0].value, 99)
        self.assertFalse(sequencer.steps[0].is_hold)
        self.assertEquals(sequencer.steps[1].value, 99)
        self.assertTrue(sequencer.steps[1].is_hold)
        # Test previous step hasn't been overridden
        self.assertEquals(sequencer.steps[2].value, 12)
        self.assertFalse(sequencer.steps[2].is_hold)

        # Test next step after non-hold step is blank
        self.assertIsNone(sequencer.steps[3].value)
        self.assertFalse(sequencer.steps[3].is_hold)
