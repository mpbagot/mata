# Import the API modules
from mod import Mod
from api import network, cmd, dimension, item, vehicle
from api.packets import *
from api.entity import *

# Import the extra mod data
from mods.default.packets import *
from mods.default.biomes import *
from mods.default.items import *
from mods.default.dimension import DefaultChunkProvider
from mods.default.server.entity import bear, npc
from mods.default.server.vehicle import horse
from mods.default.server.events import *

import util
import random
import math
import time

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
                    FetchInventoryPacket, SendPlayerImagePacket,
                    FetchPickupItem, SendPickupItem
                  ]
        for packet in packets:
            self.packetPipeline.registerPacket(packet)

        # Register the packet handler with the game
        self.gameRegistry.registerPacketHandler(self.packetPipeline)

        # Register the entities
        self.gameRegistry.registerEntity(bear.Bear())
        self.gameRegistry.registerEntity(npc.NPC())
        self.gameRegistry.registerVehicle(horse.Horse())

        # Register the items
        self.gameRegistry.registerItem(Dirt)
        self.gameRegistry.registerItem(Sword)
        self.gameRegistry.registerItem(Teeth)
        self.gameRegistry.registerItem(Gold)

    def postLoad(self):
        # Register the commands
        self.commands = [('/kick', KickPlayerCommand), ('/spawn', SpawnEntityCommand),
                         ('/create', ConstructVehicleCommand), ('/trade', TradeRequestCommand)
                        ]
        for comm in self.commands:
            self.gameRegistry.registerCommand(*comm)

        # Initialise the biomes
        self.biomes = [Ocean, Forest, City, Desert]
        # Initialise and register the DimensionHandler accordingly

        dimensionHandler = dimension.DimensionHandler(DefaultChunkProvider(self.biomes, 3), dimension.WorldMP())
        self.gameRegistry.registerDimension(dimensionHandler)

        # Register the events
        self.gameRegistry.registerEventHandler(events.onTick, 'onTick')
        self.gameRegistry.registerEventHandler(events.onPlayerDeath, 'onPlayerDeath')
        self.gameRegistry.registerEventHandler(events.onEntityDeath, 'onEntityDeath')
        self.gameRegistry.registerEventHandler(events.onPlayerLogin, 'onPlayerLogin')
        self.gameRegistry.registerEventHandler(events.onPlayerCreated, 'onPlayerCreated')
        self.gameRegistry.registerEventHandler(events.onPlayerMount, 'onPlayerMount')
        self.gameRegistry.registerEventHandler(events.onEntityDamage, 'onEntityDamage')
        self.gameRegistry.registerEventHandler(events.onEntityDamage, 'onPlayerDamage')
        self.gameRegistry.registerEventHandler(events.onDisconnect, 'onDisconnect')


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

class TradeRequestCommand(cmd.Command):
    def run(self, username, *args):
        # Username is whoever sent the command, args is everything after '/trade'
        if args:
            tradeWith = args[0]
            # Send trade request to chosen user
        else:
            # send out a local trade request to all nearby clients
            pass

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
            self.game.getWorld(dimensionId).spawnEntityInWorld(newVehicle)
        except KeyError:
            print('[ERROR] Vehicle does not exist')
