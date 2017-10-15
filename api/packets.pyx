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
        print(self.size)
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
        print(self.player.username + ' joined the server!')
        # Sync the player back to the Client
        return SyncPlayerPacketClient(self.player)

class RequestWorldPacket(Packet):
    def __init__(self, dimId=None, pos=None):
        self.pos = pos
        self.id = dimId

    def toBytes(self, buf):
        buf.write(str(self.pos).encode())
        buf.write('|'.encode())
        buf.write(self.id.to_bytes(2, 'big'))

    def fromBytes(self, data):
        pos, id = data.split('|'.encode())
        self.pos = eval(pos.decode())
        self.id = int.from_bytes(id, 'big')

    def onReceive(self, connection, game):
        worldData = game.modLoader.gameRegistry.dimensions[self.id].getWorldObj().generate(self.pos).world.map
        tileMaps = [TileMap.createFromTiles(worldData[a:a+30]) for a in range(0, len(worldData), 30)]

        return [SendWorldPacket(tileMap, self.pos, game, self.id, index+1, len(tileMaps)) for index, tileMap in enumerate(tileMaps)]


class SendWorldPacket(Packet):
    def __init__(self, tiles=None, pos=None, game=None, dimId=None, part=1, length=None):
        self.length = length
        self.tiles = tiles
        self.part = part
        self.pos = pos
        self.id = dimId
        self.game = game

    def toBytes(self, buf):
        buf.write(self.length.to_bytes(1, 'big')+b'|')
        buf.write(self.part.to_bytes(1, 'big'))
        buf.write('|'.encode())
        buf.write(self.id.to_bytes(1, 'big'))
        buf.write('|'.encode())
        # Get the biome list
        biomes = self.game.modLoader.gameRegistry.dimensions[self.id].biomes
        buf.write(self.tiles.toBytes(biomes))

    def fromBytes(self, data):
        length, part, id, *tiles = data.split('|'.encode())
        self.length = int.from_bytes(length, 'big')
        self.part = int.from_bytes(part, 'big')
        self.id = int.from_bytes(id, 'big')
        self.tiles = '|'.encode().join(tiles)

    def onReceive(self, connection, game):
        biomes = game.modLoader.gameRegistry.dimensions[self.id].biomes
        start = time.time()
        self.tiles = TileMap.fromBytes(self.tiles, biomes)
        print('took', time.time()-start, 'to get world from bytes')
        if game.world is None:
            # Handle the screen change if necessary
            game.fireEvent('onGameLoad')
            game.world = game.modLoader.gameRegistry.dimensions[self.id].getWorldObj()
            game.world.world = self.tiles
        game.player.relPos = [0, 0]

class SyncPlayerPacketClient(Packet):
    def __init__(self, player=''):
        self.player = player

    def toBytes(self, buf):
        buf.write(self.player.toBytes())

    def fromBytes(self, data):
        print('recieved a player sync packet')
        self.player = Player.fromBytes(data)

    def onReceive(self, connection, game):
        # Sync the player object on the client
        game.player.pos = self.player.pos
        game.player.health = self.player.health
        print('player set by player sync packet')
        dimId = 0
        for dim in game.modLoader.gameRegistry.dimensions:
            if dim == game.player.dimension:
                dimId = dim
        return RequestWorldPacket(dimId, self.player.pos)

class SyncPlayerPacketServer(Packet):
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
        if abs(self.player.pos[0]-serverPlayer.pos[0]) > 25 or abs(self.player.pos[1]-serverPlayer.pos[1]) > 25:
            return SyncPlayerPacketClient(serverPlayer)
        # If the player has clipped into a plant, reset their position
        world = game.modLoader.gameRegistry.dimensions[self.player.dimension].getWorldObj()

        # if world.world.map[self.player.pos[1]][self.player.pos[0]].plantIndex != -1:
        #     return SyncPlayerPacketClient(serverPlayer)

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
