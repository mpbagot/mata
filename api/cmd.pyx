class Command:
    def __init__(self, game):
        self.game = game

    def run(self, *args):
        raise NotImplementedError('[ERROR] A command has not been told to do anything')
