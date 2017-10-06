from api.packets import Packet
from api.entity import Player
from api.item import Inventory

class LoginPacket(Packet):
    def __init__(self, player=None):
        self.player = player

    def toBytes(self, buf):
        buf.write(self.player.toBytes())

    def fromBytes(self, data):
        self.player = Player.fromBytes(data)

    def onRecieve(self, connection, game):
        game.world.addPlayer(self.player)
        connection.username = self.player.username

class WorldUpdatePacket(Packet):
    def __init__(self, world=None):
        self.world = world

    def toBytes(self, buf):
        buf.write(self.world.getUpdateData())

    def fromBytes(self, data):
        self.world = data

    def onRecieve(self, connection, game):
        # Update the world on the Client side
        game.world.handleUpdate(self.world)

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

class FetchInventoryPacket(Packet):
    def __init__(self, playername=''):
        self.playername = playername

    def toBytes(self, buf):
        buf.write(self.playername.encode())

    def fromBytes(self, data):
        self.playername = data.decode()

    def onRecieve(self, connection, game):
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

    def onRecieve(self, connection, game):
        # TODO Do something with the inventory here
        pass
