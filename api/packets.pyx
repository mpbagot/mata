from api.entity import Player
from api.dimension import WorldMP
from api.biome import TileMap

import util

import time

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

    def onReceive(self, connection, side, game):
        # Set the connection's next receive size to the size gotten from this packet
        connection.setNextPacketSize(self.size)

class LoginPacket(Packet):
    def __init__(self, player=None):
        self.player = player

    def toBytes(self, buf):
        buf.write(self.player.toBytes())

    def fromBytes(self, data):
        self.player = Player.fromBytes(data)

    def onReceive(self, connection, side, game, connections):

        # TODO Add password login for certain elevated usernames

        for conn in connections:
            if connections[conn].username == self.player.username:
                return InvalidLoginPacket()

        connection.username = self.player.username

        # Add the player
        self.player = game.getWorld(0).addPlayer(self.player)

        # Fire a login event
        game.fireEvent('onPlayerLogin', self.player)
        print(self.player.username + ' joined the server!')

        # Sync the player back to the Client
        return [
                SetupClientPacket(game.getDimension(0).getBiomeSize(), game.modLoader.gameRegistry.seed),
                ResetPlayerPacket(self.player)
               ]

class SetupClientPacket(Packet):
    def __init__(self, biomeSize=0, seed=0):
        self.seed = seed
        self.size = biomeSize

    def toBytes(self, buf):
        buf.write(self.size.to_bytes(1, 'big'))
        buf.write(str(round(self.seed, 5)).encode())

    def fromBytes(self, data):
        print(data)
        self.size = data[0]
        self.seed = eval(data[1:])

    def onReceive(self, connection, side, game):
        # Set the seed and biomesize
        game.modLoader.gameRegistry.seed = self.seed
        game.getDimension(0).biomeSize = self.size
        # Fire the login event
        game.fireEvent('onPlayerLogin', game.player)

class ResetPlayerPacket(Packet):
    def __init__(self, player='', currentPlayer='' ,pos=True, hp=True, dimension=True):
        self.player = player
        if not pos:
            self.player.pos = currentPlayer.pos
            self.player.relPos = currentPlayer.relPos
        if not hp:
            self.player.health = currentPlayer.health
        if not dimension:
            self.player.dimension = currentPlayer.dimension

    def toBytes(self, buf):
        buf.write(self.player.toBytes())

    def fromBytes(self, data):
        playerData = data
        self.player = Player.fromBytes(playerData)

    def onReceive(self, connection, side, game):
        # Sync the player object on the client
        game.player.pos = self.player.pos
        game.player.health = self.player.health
        game.player.relPos = [0, 0]
        game.player.dimension = self.player.dimension

class SyncPlayerPacket(Packet):
    def __init__(self, player=''):
        self.player = player

    def toBytes(self, buf):
        buf.write(self.player.toBytes())

    def fromBytes(self, data):
        self.player = Player.fromBytes(data)

    def onReceive(self, connection, side, game):
        # Check if the player's motion is not greater than a certain threshold
        # Update their position on the server if it is ok
        # Reset them if it's not
        playerList = game.getWorld(self.player.dimension)
        serverPlayer = game.getPlayer(self.player.username)

        if abs(self.player.pos[0]-serverPlayer.pos[0]) > 5 or abs(self.player.pos[1]-serverPlayer.pos[1]) > 5:
            return ResetPlayerPacket(serverPlayer)

        if self.player.dimension != serverPlayer.dimension:
            # TODO check if it's possible for the change to have occured
            return ResetPlayerPacket(serverPlayer, self.player, pos=False)

        # If the player has clipped into a plant, reset their position
        world = game.modLoader.gameRegistry.dimensions[self.player.dimension].getWorldObj()

        # TODO change this later
        # if world.world.map[self.player.pos[1]][self.player.pos[0]].plantIndex < 0:
        #     return ResetPlayerPacket(serverPlayer)

        # Sync the player object on the server
        game.setPlayer(self.player)
        # playerIndex = game.getPlayerIndex(self.player)
        # game.modLoader.gameRegistry.dimensions[self.player.dimension].getWorldObj().players[playerIndex] = self.player

class WorldUpdatePacket(Packet):
    def __init__(self, world=None, username=''):
        self.world = world
        self.username = username

    def toBytes(self, buf):
        buf.write(self.world.getUpdateData(self.username))

    def fromBytes(self, data):
        self.world = data

    def onReceive(self, connection, side, game):
        # Update the world on the Client side
        if game.world:
            game.world.handleUpdate(self.world, game)

class SendCommandPacket(Packet):
    def __init__(self, text=''):
        self.text = text

    def toBytes(self, buf):
        buf.write(self.text.encode())

    def fromBytes(self, data):
        self.text = data.decode()

    def onReceive(self, connection, side, game):
        if self.text[0] != '/':
            self.text = '/message global '+self.text
        game.fireCommand(self.text, connection.username)

class InvalidLoginPacket(Packet):
    def toBytes(self, buf):
        pass

    def fromBytes(self, data):
        pass

    def onReceive(self, connection, side, game):
        pass

class DisconnectPacket(Packet):
    def __init__(self, message=''):
        self.message = message

    def toBytes(self, buf):
        buf.write(self.message.encode())

    def fromBytes(self, data):
        self.message = data.decode()

    def onReceive(self, connection, side, game):
        game.fireEvent('onDisconnect', self.message)
        connection.connObj.close()
        del connection
