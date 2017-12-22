from api.packets import SendCommandPacket

import util

class Command:
    def __init__(self, game):
        self.game = game

    def run(self, username, *args):
        raise NotImplementedError('[ERROR] A command has not been told to do anything')

class FailedCommand(Command):
    def run(self, username, *args):
        # If on the server, send to the client that sent the bad command
        if self.game.args.getRuntimeType() == util.SERVER:
            self.game.getModInstance('ServerMod').packetPipeline.sendToPlayer(SendCommandPacket('/message '+args[0]+' is not a valid command.'), username)
            return
        # Print an error message if on the client side
        self.game.fireCommand('/message '+args[0]+' is not a valid command.', username)

class MessageCommand(Command):
    def run(self, username, *args):
        # If on the server, send to the client that sent the bad command
        if self.game.args.getRuntimeType() == util.SERVER:
            self.game.getModInstance('ServerMod').packetPipeline.sendToAll(SendCommandPacket('/message '+' '.join(args)))
            return
        # Print an error message if on the client side
        raise NotImplementedError('[ERROR] A command has not been told to do anything')
