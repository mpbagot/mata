from api.network import Packet
from api.entity import Player
from api.item import Inventory

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
    def __init__(self, message):
        self.message = message

    def toBytes(self, buf):
        buf.write(self.message.encode())

    def fromBytes(self, data):
        self.message = data.decode()

    def onRecieve(self, packetHandler, game):
        # Open a GUI that displays the message, and disconnect them
        game.openGui(game.modLoader.mods.get('ClientMod').disconnectMessageGui, self.message)
        del packetHandler

class FetchInventoryPacket(Packet):
    def __init__(self, playername):
        self.playername = playername

    def toBytes(self, buf):
        buf.write(self.playername.encode())

    def fromBytes(self, data):
        self.playername = data.decode()

    def onRecieve(self, packetHandler, game):
        # Fetch the inventory of the required player, and send it back
        players = game.world.players
        inventory = players[[p.username for p in players].index(self.playername)].getInventory()
        return SendInventoryPacket(inventory)

class SendInventoryPacket(Packet):
    def __init__(self, inventory):
        self.inventory = inventory

    def toBytes(self, buf):
        buf.write(self.inventory.encode())

    def fromBytes(self, data):
        self.inventory = Inventory.getFromBytes(data)

    def onRecieve(self, packetHandler, game):
        # TODO Do something with the inventory here
        pass
