import util

class Command:
    def __init__(self, game):
        self.game = game

    def run(self, *args):
        raise NotImplementedError('[ERROR] A command has not been told to do anything')

class FailedCommand(Command):
    def run(self, *args):
        # If on the server, ignore
        if self.game.args.getRuntimeType() == util.SERVER:
            return
        # Print an error message if on the client side
        self.game.fireCommand('/message '+args[0]+' is not a valid command.')

class MessageCommand(Command):
    # TODO Override this in the client mod as required
    pass
