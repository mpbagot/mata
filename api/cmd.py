class Command:
    def __init__(self, text, world):
        self.text = text
        self.world = world

    def run(self, *args):
        raise NotImplementedError('[ERROR] A command has been told to not do anything?')
