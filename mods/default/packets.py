from api.packets import Packet
from api.item import Inventory, ItemStack
from api.entity import Player, Pickup

import util

class FetchPickupItem(Packet):
    def __init__(self, uuid=0):
        self.uuid = uuid

    def toBytes(self, buf):
        buf.write(self.uuid.to_bytes(8, 'big'))

    def fromBytes(self, data):
        self.uuid = int.from_bytes(data, 'big')

    def onReceive(self, connection, side, game):
        entity = game.getEntity(self.uuid)
        if not entity or not isinstance(entity, Pickup):
            return
        return SendPickupItem(self.uuid, entity.getItem())

class SendPickupItem(Packet):
    def __init__(self, uuid=0, stack=''):
        self.stack = stack
        self.uuid = uuid

    def toBytes(self, buf):
        buf.write(self.uuid.to_bytes(8, 'big'))
        buf.write(self.stack.toBytes())

    def fromBytes(self, data):
        self.uuid = int.from_bytes(data[:8], 'big')
        self.stack = data[8:]

    def onReceive(self, connection, side, game):
        entity = game.getEntity(self.uuid)
        if entity:
            self.stack = ItemStack.fromBytes(game, self.stack)
            entity.setItemstack(self.stack)

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
        if side != util.SERVER:
            game.player.setInventory(self.inventory)
        else:
            serverPlayer = game.getPlayer(connection.username)

            # Hash and compare to server-side. If equal, replace server-side, otherwise, replace client
            print('hashing client inv')
            clientInvHash = self.inventory.hashInv()
            print('hashing server inv')
            serverInvHash = serverPlayer.inventory.hashInv()

            # If the hash is a mismatch, reject the inventory
            if clientInvHash != serverInvHash:
                return SendInventoryPacket(serverPlayer.inventory)
            # Otherwise, accept it
            else:
                serverPlayer.inventory = self.inventory

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
