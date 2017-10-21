from api.entity import Player
from api.dimension import WorldMP
from api.biome import TileMap

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

    def onReceive(self, connection, game):
        # Set the connection's next receive size to the size gotten from this packet
        connection.setNextPacketSize(self.size)

class LoginPacket(Packet):
    def __init__(self, player=None):
        self.player = player

    def toBytes(self, buf):
        buf.write(self.player.toBytes())

    def fromBytes(self, data):
        self.player = Player.fromBytes(data)

    def onReceive(self, connection, game):
        connection.username = self.player.username
        # Add the player
        self.player = game.world.addPlayer(self.player)
        # Fire a login event
        game.fireEvent('onPlayerLogin', self.player)
        print(self.player.username + ' joined the server!')
        # Sync the player back to the Client
        return ResetPlayerPacket(self.player, True)

class ResetPlayerPacket(Packet):
    def __init__(self, player='', firstTime=False):
        self.player = player
        self.firstTime = firstTime

    def toBytes(self, buf):
        buf.write(self.player.toBytes())
        buf.write(b'|')
        buf.write(int(self.firstTime).to_bytes(1, 'big'))
        print(buf.getvalue())

    def fromBytes(self, data):
        print('received a player sync packet')
        print(data)
        playerData, firstTime = data.split(b'|')
        self.player = Player.fromBytes(playerData)
        self.firstTime = int.from_bytes(firstTime, 'big')

    def onReceive(self, connection, game):
        # Sync the player object on the client
        game.player.pos = self.player.pos
        game.player.health = self.player.health
        print('player set by player sync packet')
        game.player.relPos = [0, 0]
        # Fire a login event if the player has just been synced for the first time
        if self.firstTime:
            game.fireEvent('onPlayerLogin', game.player)

class SyncPlayerPacket(Packet):
    def __init__(self, player=''):
        self.player = player

    def toBytes(self, buf):
        buf.write(self.player.toBytes())

    def fromBytes(self, data):
        self.player = Player.fromBytes(data)

    def onReceive(self, connection, game):
        # Check if the player's motion is not greater than a certain threshold
        # Update their position on the server if it is ok
        # Reset them if it's not
        playerList = game.modLoader.gameRegistry.dimensions[self.player.dimension].getWorldObj().players
        serverPlayer = playerList[game.getPlayerIndex(self.player)]
        if abs(self.player.pos[0]-serverPlayer.pos[0]) > 5 or abs(self.player.pos[1]-serverPlayer.pos[1]) > 5:
            return ResetPlayerPacket(serverPlayer)
        # If the player has clipped into a plant, reset their position
        world = game.modLoader.gameRegistry.dimensions[self.player.dimension].getWorldObj()

        # if world.world.map[self.player.pos[1]][self.player.pos[0]].plantIndex != -1:
        #     return ResetPlayerPacket(serverPlayer)

        # Sync the player object on the server
        playerIndex = game.getPlayerIndex(self.player)
        game.modLoader.gameRegistry.dimensions[self.player.dimension].getWorldObj().players[playerIndex] = self.player

class DisconnectPacket(Packet):
    def __init__(self, message=''):
        self.message = message

    def toBytes(self, buf):
        buf.write(self.message.encode())

    def fromBytes(self, data):
        self.message = data.decode()

    def onReceive(self, connection, game):
        del connection
