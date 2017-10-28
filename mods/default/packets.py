from api.packets import Packet
from api.item import Inventory
from api.entity import Player

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

# TODO Fill this in
class FetchPlayerImagePacket(Packet):
    def __init__(self, player=None):
        self.player = player

    def toBytes(self, buf):
        buf.write(player.username.encode())

    def fromBytes(self, data):
        self.player = data.decode()

    def onReceive(self, connection, game):
        pass

class SendPlayerImagePacket(Packet):
    def __init__(self, player=None):
        self.player = player
        if player:
            self.playerImg = player.img

    def toBytes(self, buf):
        buf.write(self.player.toBytes()+b'|')
        buf.write(self.playerImg.__str__().encode())

    def fromBytes(self, data):
        self.player = Player.fromBytes(data.split(b'|')[0])
        self.playerImg = eval((data.split(b'|')[1]).decode())

    def onReceive(self, connection, game):
        # Store the image data in the player object
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
