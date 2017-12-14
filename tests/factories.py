class DummySequencer(object):
    pass


class DummyStep(object):
    def __init__(self, sequencer):
        self.sequencer = sequencer


class DummyNote(object):
    def __init__(self, step):
        self.step = step
