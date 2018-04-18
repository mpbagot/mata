# Import the API modules
from mod import Mod
from api import network, cmd, dimension, item, vehicle, properties
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
        self.tradeStateProperty = properties.Property(isTrading=False, waitingForConfirm=False, requests={}, tradingWith='')

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
        self.gameRegistry.registerEventHandler(events.onTickUpdateTradeRequests, 'onTick')

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
        requestingPlayer = self.game.getPlayer(username)

        pp = self.game.getModInstance('ServerMod').packetPipeline
        # TODO Dummy packet
        notifyPacket = SendCommandPacket('/message global Trade request sent.')
        tooFarPacket = SendCommandPacket('/message global Too far away to initiate trade.')
        inTradePacket = SendCommandPacket('/message global Player is already in a trade.')
        invalidEntityPacket = SendCommandPacket('/message global Invalid username. Unable to request trade.')
        invalidRequestPacket = SendCommandPacket('/message global Invalid username. Unable to accept trade.')

        # Username is whoever sent the command, args is everything after '/trade'
        if args:
            if args[0] == 'accept':
                # Respond to a trade request
                tradeWith = None
                if len(args) > 1:
                    tradeWith = args[1]
                props = requestingPlayer.getProperty('tradeState')
                if tradeWith is None:
                    # Accept the latest trade request to this user
                    requestItems = props.requests.items()
                    try:
                        # Get the index of latest time
                        index = max([a[1] for a in requestItems])
                        # Using that index, find out which player to respond to
                        tradeWith = requestItems[index][0]
                    except ValueError:
                        tradeWith = None

                if tradeWith:
                    # Accept a specific trade request
                    try:
                        props.requests.pop(tradeWith)
                    except KeyError:
                        pp.sendToPlayer(invalidRequestPacket, username)
                        return

                    # Check the initial requesting player
                    player = self.game.getPlayer(tradeWith)
                    if not player:
                        pp.sendToPlayer(invalidRequestPacket, username)

                    # Adjust the accepting player
                    props.isTrading = True
                    props.tradingWith = tradeWith
                    requestingPlayer.setProperty('tradeState', props)

                    # Adjust the initial requester
                    props = player.getProperty('tradeState')
                    props.isTrading = True
                    props.tradingWith = username
                    player.setProperty('tradeState', props)

                    # TODO Tell both clients to open trade gui and initiate trade
                    # pp.sendToPlayer(startTradePacket, username)
                    # pp.sendToPlayer(startTradePacket, tradeWith)

            else:
                # Send trade request to chosen user
                tradeWith = args[0]
                if tradeWith.isnumeric():
                    # Attempting to trade with an NPC
                    npc = self.game.getEntity(tradeWith)
                    if npc:
                        # Check that entity is an npc, is nearby and not currently in trade
                        if isinstance(npc, NPC) and util.calcDistance(requestingPlayer, npc) < 8:
                            # TODO NPC Trade state???
                            pass
                        # If the entity if a non-NPC entity (e.g, a Bear), error at the player
                        elif not isinstance(npc, NPC):
                            pp.sendToPlayer(invalidEntityPacket, username)
                        else:
                            pp.sendToPlayer(tooFarPacket, username)

                else:
                    # Attempting to trade with another player
                    player = self.game.getPlayer(tradeWith)
                    if player:
                        # Check that player is nearby and not currently in trade
                        if util.calcDistance(requestingPlayer, player) < 8:
                            props = player.getProperty('tradeState')
                            # Error if the requested user is already trading
                            if props.isTrading:
                                pp.sendToPlayer(inTradePacket, username)
                                return

                            # Store the request
                            props.requests[username] = time.time()
                            player.setProperty('tradeState', props)

                            # Notify the player
                            pp.sendToPlayer(notifyPacket, tradeWith)
                        else:
                            # Show player an error/warning
                            pp.sendToPlayer(tooFarPacket, username)
                    else:
                        # Show player an error/warning if username is invalid
                        pp.sendToPlayer(invalidEntityPacket, username)

        else:
            # Send out a local trade request to all nearby clients
            nearby = self.game.getWorld(requestingPlayer.dimension).getPlayersNear(requestingPlayer.pos, 12)
            for player in nearby:
                props = player.getProperty('tradeState')
                # Skip players that are already in trade
                if props.isTrading:
                    continue

                props.requests[username] = time.time()
                player.setProperty('tradeState', props)

            pp.sendToNearby(notifyPacket, username, 12)

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
