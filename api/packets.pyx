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

    def onReceive(self, packetHandler, connection):
        '''
        Run any required logic upon receiving the packet
        '''
        raise NotImplementedError('onReceive method is empty in a packet class!')

class ByteSizePacket(Packet):
    def __init__(self, size=0):
        self.size = size

    def toBytes(self, buf):
        buf.write(self.size.to_bytes(2, 'big'))

    def fromBytes(self, data):
        self.size = int.from_bytes(data, 'big')

    def onReceive(self, connection, game):
        # Set the connection's next receive size to the size gotten from this packet
        connection.setNextPacketSize(self.size)

class LoginPacket(Packet):
    def __init__(self, player=None):
        self.player = player

    def toBytes(self, buf):
        buf.write(self.player.toBytes())

    def fromBytes(self, data):
        self.player = Player.fromBytes(data)

    def onReceive(self, connection, game):
        connection.username = self.player.username
        # Add the player
        self.player = game.world.addPlayer(self.player)
        print(self.player.username + ' joined the server!')
        # Sync the player back to the Client
        return SyncPlayerPacketClient(self.player)

class RequestWorldPacket(Packet):
    def __init__(self, pos=None):
        self.pos = pos

    def toBytes(self, buf):
        buf.write(str(self.pos).encode())

    def fromBytes(self, data):
        self.pos = eval(data.decode())

    def onReceive(self, connection, game):
        return SendWorldPacket(game.world, self.pos)

class SendWorldPacket(Packet):
    def __init__(self, world=None, pos=None):
        self.world = world
        self.pos = pos

    def toBytes(self, buf):
        buf.write(self.world.generate(self.pos).toBytes(self.pos))

    def fromBytes(self, data):
        print(data)
        self.world = WorldMP.fromBytes(data)

    def onReceive(self, connection, game):
        if game.world is None:
            # Handle the screen change if necessary
            game.openGui(game.getModInstance('ClientMod').gameGui, game)
            game.world = self.world
        else:
            game.world.world = self.world.world
        game.player.relPos = [0, 0]

class SyncPlayerPacketClient(Packet):
    def __init__(self, player=''):
        self.player = player

    def toBytes(self, buf):
        buf.write(self.player.toBytes())

    def fromBytes(self, data):
        print('recieved a player sync packet')
        self.player = Player.fromBytes(data)

    def onReceive(self, connection, game):
        # Sync the player object on the client
        game.player.pos = self.player.pos
        game.player.health = self.player.health
        print('player set by player sync packet')
        return RequestWorldPacket(self.player.pos)

class SyncPlayerPacketServer(Packet):
    def __init__(self, player=''):
        self.player = player

    def toBytes(self, buf):
        buf.write(self.player.toBytes())

    def fromBytes(self, data):
        self.player = Player.fromBytes(data)

    def onReceive(self, connection, game):
        # Sync the player object on the server
        playerIndex = game.world.getPlayerIndex(self.player.username)
        game.world.players[playerIndex] = self.player

class DisconnectPacket(Packet):
    def __init__(self, message=''):
        self.message = message

    def toBytes(self, buf):
        buf.write(self.message.encode())

    def fromBytes(self, data):
        self.message = data.decode()

    def onReceive(self, connection, game):
        # Open a GUI that displays the message, and disconnect them
        game.openGui(game.getModInstance('ClientMod').disconnectMessageGui, self.message)
        del connection
