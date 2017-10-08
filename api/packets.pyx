from api.entity import Player
from api.dimension import WorldMP

class Packet:
    def toBytes(self, buf):
        '''
        Convert the data to a bytestring and write it to a buffer
        '''
        raise NotImplementedError('toBytes method is empty in a packet class!')

    def fromBytes(self, data):
        '''
        Read the data from the binary buffer, and convert it to a usable form
        '''
        raise NotImplementedError('fromBytes method is empty in a packet class!')

    def onRecieve(self, packetHandler, connection, game):
        '''
        Run any required logic upon receiving the packet
        '''
        raise NotImplementedError('onRecieve method is empty in a packet class!')

class ByteSizePacket(Packet):
    def __init__(self, size=0):
        self.size = size

    def toBytes(self, buf):
        buf.write(self.size.to_bytes(2, 'big'))

    def fromBytes(self, data):
        self.size = int.from_bytes(data.encode(), 'big')

    def onRecieve(self, connection, game):
        # Set the connection's next recieve size to the size gotten from this packet
        connection.setNextPacketSize(self.size)

class ConfirmPacket(Packet):
    def toBytes(self, buf):
        pass

    def fromBytes(self, data):
        pass

    def onRecieve(self, connection, game):
        pass

class LoginPacket(Packet):
    def __init__(self, player=None):
        self.player = player

    def toBytes(self, buf):
        buf.write(self.player.toBytes())

    def fromBytes(self, data):
        self.player = Player.fromBytes(data)

    def onRecieve(self, connection, game):
        connection.username = self.player.username
        game.world.addPlayer(self.player)
        print(self.player.username, 'joined the server!')
        return SendWorldPacket(game.world)

class RequestWorldPacket(Packet):
    def __init__(self, pos=None):
        self.pos = pos

    def toBytes(self, buf):
        buf.write(str(self.pos).encode())

    def fromBytes(self, data):
        self.pos = eval(data.decode())

    def onRecieve(self, connection, game):
        return SendWorldPacket(game.world, self.pos)

class SendWorldPacket(Packet):
    def __init__(self, world=None, pos=None):
        self.world = world
        self.pos = pos

    def toBytes(self, buf):
        buf.write(self.world.toBytes(self.pos))

    def fromBytes(self, data):
        self.world = WorldMP.fromBytes(data)

    def onRecieve(self, connection, game):
        if game.world is None:
            game.world = self.world
        else:
            game.world.world = self.world.world
        game.openGui(game.getModInstance('ClientMod').gameGui, game)

class DisconnectPacket(Packet):
    def __init__(self, message=''):
        self.message = message

    def toBytes(self, buf):
        buf.write(self.message.encode())

    def fromBytes(self, data):
        self.message = data.decode()

    def onRecieve(self, connection, game):
        # Open a GUI that displays the message, and disconnect them
        game.openGui(game.getModInstance('ClientMod').disconnectMessageGui, self.message)
        del connection
