from api.network import Packet

'''
Notes about Packets for later
# Add the other headers to a packet
    buf.write('{"type":"{}","data":"'.format(packet.__class__.__name__).encode())
    toBytes(buf)
    buf.write('"}'.encode())

# Get the data from a packet
    data = buf.getvalue().decode()[1:-1]
    dataDictionary = {a.split(':')[0][1:-1] : a.split(':')[1][1:-1] for a in data.split(',')}
    data = dataDictionary['data']
'''

class ByteSizePacket(Packet):
    def __init__(self, size):
        self.size = size

    def toBytes(self, buf):
        buf.write(self.size.to_bytes(2, 'big'))

    def fromBytes(self, data):
        self.size = int.from_bytes(data.encode(), 'big')

    def onRecieve(self, packetHandler, game):
        # Set the PacketHandler's next recieve size to the size gotten from this packet
        packetHandler.setNextPacketSize(self.size)

class LoginPacket(Packet):
    def __init__(self, player):
        self.player = player

    def toBytes(self, buf):
        buf.write(self.player.toBytes())

    def fromBytes(self, data):
        self.player = Player.fromBytes(data)

    def onRecieve(self, packetHandler, game):
        game.world.addPlayer(self.player)

class WorldUpdatePacket(Packet):
    def __init__(self, world):
        self.world = world

    def toBytes(self, buf):
        buf.write(self.world.getUpdateData())

    def fromBytes(self, data):
        self.world = data

    def onRecieve(self, packetHandler, game):
        # Update the world on the Client side
        game.world.handleUpdate(self.world)

class ConfirmPacket(Packet):
    def toBytes(self, buf):
        pass

    def fromBytes(self, data):
        pass

    def onRecieve(self, packetHandler, game):
        pass

class DisconnectPacket(Packet):
    def toBytes(self, buf):
        pass

    def fromBytes(self, data):
        pass

    def onRecieve(self, packetHandler, game):
        del packetHandler
