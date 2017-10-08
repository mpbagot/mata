class Command:
    def __init__(self, game):
        self.game = game

    def run(self, *args):
        raise NotImplementedError('[ERROR] A command has been told to not do anything?')
