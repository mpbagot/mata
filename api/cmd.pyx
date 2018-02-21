from api.packets import SendCommandPacket

import util

class Command:
    def __init__(self, game):
        self.game = game

    def run(self, username, *args):
        raise NotImplementedError('[ERROR] A command has not been told to do anything')

class FailedCommand(Command):
    def run(self, username, *args):
        # Send a failure message back to the client
        self.game.packetPipeline.sendToPlayer(SendCommandPacket('/message global '+args[0]+' is not a valid command.'), username)
        return

class MessageCommand(Command):
    def run(self, username, *args):
        # Redirect the message if on the server
        if self.game.args.getRuntimeType() == util.SERVER:
          pp = self.game.packetPipeline
          # Send messages back to one or more clients based on the message mode
          mode = args[0]
          args = [args[0], '<{}>'.format(username)]+list(args[1:])
          if mode == 'global':
              pp.sendToAll(SendCommandPacket('/message '+' '.join(args)))
          elif mode == 'local':
              pp.sendToNearby(SendCommandPacket('/message '+' '.join(args)), username)
          else:
              # Send /message <username> message here to the user
              # Send /message <user> message here to username
              pp.sendToPlayer(SendCommandPacket('/message '+' '.join(args)), username)
              pp.sendToPlayer(SendCommandPacket('/message {} {}'.format(username, ' '.join(args[1:]))), args[0])
