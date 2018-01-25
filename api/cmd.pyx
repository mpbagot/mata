from api.packets import SendCommandPacket

import util

class Command:
    def __init__(self, game):
        self.game = game

    def run(self, username, *args):
        raise NotImplementedError('[ERROR] A command has not been told to do anything')

class FailedCommand(Command):
    def run(self, username, *args):
        # Let onCommand hooks handle it
        return

class MessageCommand(Command):
    def run(self, username, *args):
        # Let onCommand hooks handle it
        return
