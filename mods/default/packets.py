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
        inventory = players[[p.username for p in players].index(self.playername)].getInventory()
        return SendInventoryPacket(inventory)

class SendInventoryPacket(Packet):
    def __init__(self, inventory=None):
        self.inventory = inventory

    def toBytes(self, buf):
        buf.write(self.inventory.encode())

    def fromBytes(self, data):
        self.inventory = Inventory.getFromBytes(data)

    def onReceive(self, connection, game):
        # TODO Do something with the inventory here
        pass
