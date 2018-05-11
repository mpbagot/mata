from api.packets import Packet, SendCommandPacket
from api.item import Inventory, ItemStack
from api.entity import Player, Pickup

import util

from copy import deepcopy

class ConfirmTradePacket(Packet):
    # Sent when the initiator is asking for confirmation
    def __init__(self, inv1=None, inv2=None):
        self.inv1 = inv1
        self.inv2 = inv2

    def toBytes(self, buf):
        buf.write(self.inv1.toBytes())
        buf.write(b'|||')
        buf.write(self.inv2.toBytes())

    def fromBytes(self, data):
        self.inv1, self.inv2 = data.split(b'|||')[:2]

    def onReceive(self, connection, side, game):
        self.inv1 = Inventory.fromBytes(game, self.inv1)
        self.inv2 = Inventory.fromBytes(game, self.inv2)

        if side == util.SERVER:
            player = game.getPlayer(connection.username)
            if not player:
                return

            # If received by the server, just redirect it through to the client
            otherPlayername = player.getProperty('tradeState').tradingWith
            game.getModInstance('ServerMod').packetPipeline.sendToPlayer(self, otherPlayername)

        else:
            if game.getGui()[0] == game.getModInstance('ClientMod').tradeGui:
                # If received by a client, set the inventories and let the player respond
                game.getGui()[1].inv1 = self.inv1
                game.getGui()[1].inv2 = self.inv2
                game.getGui()[1].offer = True

                game.getGui()[1].buttons, game.getGui()[1].offerButtons = game.getGui()[1].offerButtons, game.getGui()[1].buttons

class EndTradePacket(Packet):
    def toBytes(self, buf):
        buf.write(b'a')

    def fromBytes(self, buf):
        pass

    def onReceive(self, connection, side, game):
        if side != util.SERVER:
            return

        player = game.getPlayer(connection.username)
        if not player:
            return

        cleanProps = deepcopy(game.getModInstance('ServerMod').tradeStateProperty)

        # Clear out the main player (keeping pending trade requests)
        props = player.getProperty('tradeState')
        otherPlayername = props.tradingWith
        newProps = deepcopy(cleanProps)
        newProps.requests = props.requests
        player.setProperty('tradeState', newProps)

        # Then clear out the other trading player
        player = game.getPlayer(otherPlayername)
        if not player:
            return

        props = player.getProperty('tradeState')
        newProps = deepcopy(cleanProps)
        newProps.requests = props.requests
        player.setProperty('tradeState', newProps)

class RespondTradePacket(Packet):
    # Sent when the acceptor responds to the confirmation
    def __init__(self, accept=False, inv1=None, inv2=None):
        self.response = bool(accept)
        self.inv1 = inv1
        self.inv2 = inv2

    def toBytes(self, buf):
        buf.write(self.response.to_bytes(1, 'big'))
        buf.write(self.inv1.toBytes())
        buf.write(b'|||')
        buf.write(self.inv2.toBytes())

    def fromBytes(self, data):
        self.response = bool(data[0])
        self.inv1, self.inv2 = data[1:].split(b'|||')[:2]

    def onReceive(self, connection, side, game):
        self.inv1 = Inventory.fromBytes(game, self.inv1)
        self.inv2 = Inventory.fromBytes(game, self.inv2)

        if side != util.SERVER:
            # If the client is still in the tradeGui, close the "Making offer..."
            # thing and set the inventories
            if game.getGui()[0] == game.getModInstance('ClientMod').tradeGui:
                game.getGui()[1].offer = None
                # Set the inventories
                game.getGui()[1].inv1 = self.inv1
                game.getGui()[1].inv2 = self.inv2

                game.getGui()[1].buttons[0].enabled = True

        else:
            # Get the accepting player's inventory
            player = game.getPlayer(connection.username)
            if not player:
                return
            serverInv1 = player.getInventory()
            player2 = game.getPlayer(player.getProperty('tradeState').tradingWith)
            serverInv2 = player2.getInventory()
            # If they accepted the trade, verify the inventories, then send them to the client
            if self.response:
                # Hash and confirm the trading
                givenInvsHash = Inventory.addInventory(self.inv1, self.inv2, True)[0].hashInv()
                serverInvsHash = Inventory.addInventory(serverInv1, serverInv2, True)[0].hashInv()

                if givenInvsHash == serverInvsHash:
                    # Get the other player in the trade and send the following packet to them
                    packet = RespondTradePacket(True, self.inv1, self.inv2)
                    game.getModInstance('ServerMod').packetPipeline.sendToPlayer(packet, player2.name)

                    # Send notice to primary trading player
                    packet = SendCommandPacket('/message ' + player.name + ' Trade accepted.')
                    game.getModInstance('ServerMod').packetPipeline.sendToPlayer(packet, player2.name)

                    return SendCommandPacket('/message ' + player2.name + ' Trade accepted.')
                else:
                    # If the hashes differ, throw a Decline response
                    self.response = False

                    # and send a message to each client (unknown error occurred)
                    players = [player, player2]
                    packets = [SendCommandPacket('/message ' + players[1-a].name + ' Unknown error occurred') for a in range(len(players))]
                    for p, packet in enumerate(packets):
                        game.getModInstance('ServerMod').packetPipeline.sendToPlayer(packet, players[p].name)

            # If the other player has denied the trade, reset the inventories
            # on the primary trader's client
            if not self.response:
                # Get the other player in the trade and send the following packet to them
                packet = RespondTradePacket(False, serverInv1, serverInv2)
                game.getModInstance('ServerMod').packetPipeline.sendToPlayer(packet, player2.name)

                # Send notice to primary trading player
                packet = SendCommandPacket('/message ' + player.name + ' Trade declined.')
                game.getModInstance('ServerMod').packetPipeline.sendToPlayer(packet, player2.name)

                return SendCommandPacket('/message ' + player2.name + ' Trade declined.')

class StartTradePacket(Packet):
    def __init__(self, other='', isInitiator=False):
        self.other = other
        self.isInitiator = isInitiator

    def toBytes(self, buf):
        buf.write(int(self.isInitiator).to_bytes(1, 'big'))
        buf.write(self.other.encode())

    def fromBytes(self, data):
        self.isInitiator = bool(data[0])
        self.other = data[1:].decode()

    def onReceive(self, connection, side, game):
        # Do one more check that the other player exists
        other = game.getPlayer(self.other) or game.getEntity(self.other)
        if not other:
            return

        # Open the trade gui here
        game.openGui(game.getModInstance('ClientMod').tradeGui, game, self.other, self.isInitiator)
        # Fetch the inventories
        return [
                FetchInventoryPacket(game.player.name),
                FetchInventoryPacket(self.other)
               ]

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
        player = game.getPlayer(self.playername)
        if player:
            inventory = player.getInventory()
        # If the player doesn't exist, try searching the entities
        elif self.playername.isnumeric():
            npc = game.getEntity(int(self.playername))
            inventory = npc.getInventory()

        if inventory:
            return SendInventoryPacket(self.playername, inventory)

class SendInventoryPacket(Packet):
    def __init__(self, playername='', inventory=None):
        self.inventory = inventory
        self.playername = str(playername)

    def toBytes(self, buf):
        buf.write(len(self.playername).to_bytes(1, 'big') + self.playername.encode())
        buf.write(self.inventory.toBytes())

    def fromBytes(self, data):
        nameLen = data[0]
        self.playername = data[1:1 + nameLen].decode()
        self.inventory = data[1 + nameLen:]

    def onReceive(self, connection, side, game):
        # Decode and store the inventory in the client side player
        self.inventory = Inventory.fromBytes(game, self.inventory)
        if side != util.SERVER:
            # If the player has requested their own inventory, just set it and let them use it from there
            if game.player.name == self.playername:
                game.player.setInventory(self.inventory)
            # Otherwise, look up the correct player and store it in them
            else:
                player = game.getPlayer(self.playername)
                if player:
                    player.setInventory(self.inventory)
                elif self.playername.isnumeric():
                    # If the playername is actually a uuid, try to find the corresponding entity
                    npc = game.getEntity(int(self.playername))
                    if npc:
                        npc.setInventory(self.inventory)
        else:
            serverPlayer = game.getPlayer(self.playername)

            # Hash and compare to server-side. If equal, replace server-side, otherwise, replace client
            clientInvHash = self.inventory.hashInv()
            serverInvHash = serverPlayer.inventory.hashInv()

            # If the hash is a mismatch, reject the inventory
            if clientInvHash != serverInvHash:
                return SendInventoryPacket(self.playername, serverPlayer.inventory)
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
