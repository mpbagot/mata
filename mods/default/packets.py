from api.packets import Packet
from api.item import Inventory

class WorldUpdatePacket(Packet):
    def __init__(self, world=None):
        self.world = world

    def toBytes(self, buf):
        buf.write(self.world.getUpdateData())

    def fromBytes(self, data):
        self.world = data

    def onReceive(self, connection, game):
        # Update the world on the Client side
        if game.world:
            game.world.handleUpdate(self.world)

class FetchInventoryPacket(Packet):
    def __init__(self, playername=''):
        self.playername = playername

    def toBytes(self, buf):
        buf.write(self.playername.encode())

    def fromBytes(self, data):
        self.playername = data.decode()

    def onReceive(self, connection, game):
        # Fetch the inventory of the required player, and send it back
        players = game.world.players
        inventory = players[game.getPlayerIndex(self.playername)].getInventory()
        return SendInventoryPacket(inventory)

class SendPlayerImagePacket(Packet):
    def __init__(self, player=None):
        self.player = player
        self.playerImg = player.img

    def toBytes(self, buf):
        buf.write(self.player.toBytes()+b'|')
        buf.write(self.playerImg.__str__().encode())

    def fromBytes(self, data):
        self.player = Player.fromBytes(data.split(b'|')[0])
        self.playerImg = eval((data.split(b'|')[1]).decode())

    def onReceive(self, connection, game):
        # Store the image data in the server side player
        game.world.players[game.getPlayerIndex(self.player)].img = self.playerImg

class SendInventoryPacket(Packet):
    def __init__(self, inventory=None):
        self.inventory = inventory

    def toBytes(self, buf):
        buf.write(self.inventory.toBytes())

    def fromBytes(self, data):
        self.inventory = Inventory.fromBytes(data)

    def onReceive(self, connection, game):
        # Store the inventory in the client side player
        game.player.setInventory(self.inventory)
