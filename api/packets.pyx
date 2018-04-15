from api.entity import Player
from api.vehicle import Vehicle
from api.dimension import WorldMP
from api.biome import TileMap

import util

from datetime import datetime
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

class LoginPacket(Packet):
    def __init__(self, player=None):
        self.player = player

    def toBytes(self, buf):
        buf.write(self.player.toBytes())

    def fromBytes(self, data):
        self.player = Player.fromBytes(data)

    def onReceive(self, connection, side, game, connections):

        # TODO Add password login for certain elevated usernames

        # TODO Fix the connection overlap that prevents relogging in
        # and the second packetPipeline from connecting
        print(self.player.name)

        print(connections)
        for conn in connections:
            if connections[conn].username == self.player.name:
                print('existing connection found')
                return InvalidLoginPacket()

        connection.username = self.player.name

        # Add the player
        self.player = game.getWorld(0).addPlayer(self.player)

        # Fire a login event
        game.fireEvent('onPlayerLogin', self.player)
        print(self.player.name + ' joined the server!')

        # Sync the player back to the Client
        return [
                SetupClientPacket(game.getDimension(0).getBiomeSize(), game.modLoader.gameRegistry.seed),
                ResetPlayerPacket(self.player)
               ]

class SetupConnPacket(Packet):
    def __init__(self, player=None):
        self.player = player

    def toBytes(self, buf):
        buf.write(self.player.toBytes())

    def fromBytes(self, data):
        self.player = Player.fromBytes(data)

    def onReceive(self, connection, side, game, connections):
        # Check if this has already been done in this pipeline
        for conn in connections:
            if connections[conn].username == self.player.name:
                return InvalidLoginPacket()

        # If not, set the connection username
        connection.username = self.player.name

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
        game.player.dimension = self.player.dimension

class SyncPlayerPacket(Packet):
    def __init__(self, player=''):
        self.player = player

    def toBytes(self, buf):
        buf.write(self.player.toBytes())

    def fromBytes(self, data):
        self.player = Player.fromBytes(data)

    def onReceive(self, connection, side, game):
        # Update their status on the server if everything is ok
        # Reset them if it's not
        if connection.username and self.player.name != connection.username:
            # This is someone trying to mess with another player, do nothing
            return

        playerList = game.getWorld(self.player.dimension)
        serverPlayer = game.getPlayer(self.player.name)

        # Get the deltaTime, and deltaTicks since last synchronisation
        if isinstance(serverPlayer.synced, datetime):
            deltaTime = int((datetime.now()-serverPlayer.synced).total_seconds()*1000)
        else:
            deltaTime = 4000/util.FPS
        deltaTicks = round(deltaTime*(util.FPS/1000))

        # Write the new sync time (in case we need to reset)
        serverPlayer.synced = datetime.now()

        # Check if the player's motion is not greater than a certain threshold
        threshold = serverPlayer.getSpeed(game)*(deltaTicks+2) + 0.0005 # <- Add this tiny extra bit to account for float imprecision
        if max([abs(self.player.pos[a]-serverPlayer.pos[a]) for a in (0, 1)]) > threshold:
            return ResetPlayerPacket(serverPlayer)

        if self.player.dimension != serverPlayer.dimension:
            # TODO check if it's possible for the dimension shift to have occured
            return ResetPlayerPacket(serverPlayer, self.player, pos=False)

        # If the player has clipped into a plant, reset their position
        world = game.modLoader.gameRegistry.dimensions[self.player.dimension].getWorldObj()

        # TODO Add check for player collision with plants, buildings etc
        # if world.world.map[self.player.pos[1]][self.player.pos[0]].plantIndex < 0:
        #     return ResetPlayerPacket(serverPlayer)

        # Sync the player object on the server
        serverPlayer.pos = self.player.pos
        serverPlayer.dimension = self.player.dimension
        serverPlayer.health = self.player.health

class MountPacket(Packet):
    def __init__(self, vehicle=None, player=None):
        if isinstance(vehicle, Vehicle):
            vehicle = vehicle.uuid
        if isinstance(player, Player):
            player = player.name

        self.entity = str(vehicle)
        self.player = str(player)

    def toBytes(self, buf):
        buf.write(self.entity.encode()+b'|')
        buf.write(self.player.encode())

    def fromBytes(self, data):
        self.entity, self.player = data.decode().split('|')

    def onReceive(self, connection, side, game):
        # Set up the entity and player values
        print(self.entity)
        if self.entity != 'None':
            self.entity = game.getVehicle(self.entity)
        else:
            self.entity = None

        self.player = game.getPlayer(self.player)

        # Adjust on the client
        if side != util.SERVER:
            # Accept the changes without question
            game.player.ridingEntity = self.entity
            if self.entity is not None:
                success = self.entity.mountRider(game.player, game)
                game.fireEvent('onPlayerMount', self.player, self.entity, success, 'mount')
            else:
                success = self.entity.unmountRider(game.player)
                game.fireEvent('onPlayerMount', self.player, self.entity, success, 'dismount')

        # Adjust on the server
        elif side == util.SERVER and self.player:
            # Attempt to connect a player to a vehicle
            if self.entity is not None:
                # Calculate the distance between the player and vehicle
                pos = [(self.entity.pos[a]-self.player.pos[a])**2 for a in [0, 1]]
                dist = sum(pos)**.5
                # Check for equal dimension and distance
                if self.entity.dimension == self.player.dimension and dist < 8:
                    print('Mounting player {} to vehicle {}'.format(self.player.name, self.entity.uuid))
                    # If all prerequisites are met, connect the player to the vehicle
                    success = self.entity.mountRider(self.player, game)
                    game.fireEvent('onPlayerMount', self.player, self.entity, success, 'mount')
                else:
                    return MountPacket()

            else:
                print('dismounting player from entity')
                # Dismount the entity/player
                if self.player.ridingEntity:
                    success = game.getVehicle(self.player.ridingEntity).unmountRider(self.player)
                game.fireEvent('onPlayerMount', self.player, self.entity, success, 'dismount')

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
        if side == util.SERVER:
            game.fireEvent('onDisconnect', connection.username)
        else:
            game.fireEvent('onDisconnect', self.message)
        connection.connObj.close()
        del connection
