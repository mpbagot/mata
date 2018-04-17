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

    def onReceive(self, connection, side, game):
        # Fetch the inventory of the required player, and send it back
        inventory = game.getPlayer(self.playername).getInventory()
        return SendInventoryPacket(inventory)

class SendInventoryPacket(Packet):
    def __init__(self, inventory=None):
        self.inventory = inventory

    def toBytes(self, buf):
        buf.write(self.inventory.toBytes())

    def fromBytes(self, data):
        self.inventory = data

    def onReceive(self, connection, side, game):
        # Decode and store the inventory in the client side player
        self.inventory = Inventory.fromBytes(game, self.inventory)
        game.player.setInventory(self.inventory)

class FetchPlayerImagePacket(Packet):
    def __init__(self, player=None):
        self.player = player

    def toBytes(self, buf):
        buf.write(self.player.name.encode())

    def fromBytes(self, data):
        self.player = data.decode()

    def onReceive(self, connection, side, game):
        player = game.getPlayer(self.player)
        return SendPlayerImagePacket(player)

class SendPlayerImagePacket(Packet):
    def __init__(self, player=None):
        if player:
            self.playerName = player.name
            self.playerImg = player.img

    def toBytes(self, buf):
        buf.write(self.playerName.encode()+b'|')
        buf.write(self.playerImg.__str__().encode())

    def fromBytes(self, data):
        self.playerName = data.split(b'|')[0].decode()
        self.playerImg = eval((data.split(b'|')[1]).decode())

    def onReceive(self, connection, side, game):
        # Store the image data in the player object
        game.getPlayer(self.playerName).img = self.playerImg
