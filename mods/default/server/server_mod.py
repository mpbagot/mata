# Import the API modules
from mod import Mod
from api import network, cmd, dimension, item, vehicle
from api.packets import *

# Import the extra mod data
from mods.default.packets import *
from mods.default.biomes import *
from mods.default.items import *
from mods.default.dimension import DefaultChunkProvider
from mods.default.server.entity import bear
from mods.default.server.vehicle import horse

import util

class ServerMod(Mod):
    modName = 'ServerMod'

    def preLoad(self):
        pass

    def load(self):
        # Initialise the packet pipeline
        self.packetPipeline = network.PacketHandler(self.game, util.SERVER, self.game.getOpenPort())
        # Register the valid packet classes
        packets = [
                    FetchPlayerImagePacket, SendInventoryPacket,
                    FetchInventoryPacket, SendPlayerImagePacket
                  ]
        for packet in packets:
            self.packetPipeline.registerPacket(packet)

        # Register the packet handler with the game
        self.gameRegistry.registerPacketHandler(self.packetPipeline)

        # Register the entities
        self.gameRegistry.registerEntity(bear.Bear())
        self.gameRegistry.registerVehicle(horse.Horse())

        # Register the items
        self.gameRegistry.registerItem(Dirt)
        self.gameRegistry.registerItem(Sword)

    def postLoad(self):
        # Register the commands
        self.commands = [('/kick', KickPlayerCommand), ('/spawn', SpawnEntityCommand), ('/create', ConstructVehicleCommand)]
        for comm in self.commands:
            self.gameRegistry.registerCommand(*comm)

        # Initialise the biomes
        self.biomes = [Ocean, Forest, City, Desert]
        # Initialise and register the DimensionHandler accordingly

        dimensionHandler = dimension.DimensionHandler(DefaultChunkProvider(self.biomes, 3), dimension.WorldMP())
        self.gameRegistry.registerDimension(dimensionHandler)

        # Register the events
        self.gameRegistry.registerEventHandler(onTick, 'onTick')
        self.gameRegistry.registerEventHandler(onPlayerDeath, 'onPlayerDeath')
        self.gameRegistry.registerEventHandler(onPlayerLogin, 'onPlayerLogin')
        self.gameRegistry.registerEventHandler(onPlayerMount, 'onPlayerMount')
        self.gameRegistry.registerEventHandler(onDisconnect, 'onDisconnect')

def onTick(game, tick):
    if tick%(util.FPS//6) == 0:
        # Send server updates to all of the connected clients 6 times a second
        pp = game.packetPipeline
        connections = pp.connections.keys()
        # Loop the keys
        for c in list(connections):
            # Get the connection object from the dictionary
            conn = pp.connections.get(c)
            # If it has been deleted by the other thread during iteration, skip it
            if not conn:
                continue
            # If the player has logged in, send the world update data to them
            if conn.username:
                player = game.getPlayer(conn.username)
                # Customise the packet for each player
                packet = WorldUpdatePacket(game.getWorld(player.dimension), player)
                pp.sendToPlayer(packet, conn.username)

def onPlayerMount(game, player, entity, success, mode):
    '''
    Event Hook: onPlayerMount
    Sync the new player position to the client when the player mounts an entity
    '''
    # If the player is mounting an entity (as opposed to dismounting)
    if success and mode == 'mount':
        # Set the player position
        player.setPos(entity.pos)

        # Create and send the sync packet
        packet = ResetPlayerPacket(player)
        game.packetPipeline.sendToPlayer(packet, player.name)

def onPlayerDeath(game, player):
    '''
    Event Hook: onPlayerDeath
    Close the connection to the client and
    '''
    # Close the connection to the client from the server
    pp = game.packetPipeline
    pp.sendToPlayer(DisconnectPacket('You have died'), player.name)
    game.fireEvent('onDisconnect', player.name)

def onPlayerLogin(game, player):
    '''
    Event Hook: onPlayerLogin
    Print a little message when a player connects
    '''
    print(player.name + ' joined the server!')

def onDisconnect(game, username):
    '''
    Event Hook: onDisconnect
    Print a little message in the server console
    '''
    print('Client player "' + username + '" has disconnected')

    player = game.getPlayer(username)
    # Unmount the player
    if player.ridingEntity:
        vehicle = game.getVehicle(player.ridingEntity)
        if vehicle:
            vehicle.unmountRider(player)
        player.ridingEntity = None
    # TODO Move the player out of danger. Somehow...

    game.packetPipeline.closeConnection(username)
    game.getModInstance('ServerMod').packetPipeline.closeConnection(username)

class KickPlayerCommand(cmd.Command):
    def run(self, username, *args):
        pp = self.game.packetPipeline
        # Send a failure message if the user doesn't have elevated privileges
        if username not in open('mods/default/server/elevated_users').read().split('\n')[:-1]:
            pp.sendToPlayer(SendCommandPacket('/message You do not have permission to use that command'), username)
            return

        for player in args:
            # Loop the players, and kick them by deleting the PacketHandler
            # Delete the connection from the server to the client
            pp.sendToPlayer(DisconnectPacket('You have been kicked from the server.'), player)
            self.game.fireEvent('onDisconnect', player.name)
            break

class SpawnEntityCommand(cmd.Command):
    def run(self, username, *args):
        entityName = args[0]
        dimensionId = self.game.getPlayer(username).dimension
        try:
            newEntity = self.game.modLoader.gameRegistry.entities[entityName]()
            newEntity.uuid = self.game.modLoader.getUUIDForEntity(newEntity)
            self.game.getWorld(dimensionId).spawnEntityInWorld(newEntity)
        except KeyError:
            print('[ERROR] Entity does not exist')


class ConstructVehicleCommand(cmd.Command):
    def run(self, username, *args):
        vehicleName = args[0]
        dimensionId = self.game.getPlayer(username).dimension
        try:
            newVehicle = self.game.modLoader.gameRegistry.vehicles[vehicleName]()
            newVehicle.uuid = self.game.modLoader.getUUIDForEntity(newVehicle)
            self.game.getWorld(dimensionId).spawnEntityInWorld(newVehicle, 'vehicle')
        except KeyError:
            print('[ERROR] Vehicle does not exist')
