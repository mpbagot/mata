# Import the API modules
from mod import Mod
from api import network, biome, cmd, dimension, entity, item, properties, vehicle
from api.packets import *

# Import the extra mod data
from mods.default.packets import *
from mods.default.biomes import *
import util

class ServerMod(Mod):
    modName = 'ServerMod'

    def preLoad(self):
        pass

    def load(self):
        # Initialise the packet pipeline
        self.packetPipeline = network.PacketHandler(self.game, util.SERVER)
        # Register the valid packet classes
        self.packetPipeline.registerPacket(WorldUpdatePacket)
        self.packetPipeline.registerPacket(SendPlayerImagePacket)
        self.packetPipeline.registerPacket(FetchPlayerImagePacket)
        # Register the packet handler with the game
        self.gameRegistry.registerPacketHandler(self.packetPipeline)

    def postLoad(self):
        # Register the commands
        self.commands = [('/kick', KickPlayerCommand)]
        for comm in self.commands:
            self.gameRegistry.registerCommand(*comm)

        # Initialise the biomes
        self.biomes = [Ocean, Forest, City, Desert]
        # Initialise and register the DimensionHandler accordingly
        dimensionHandler = dimension.DimensionHandler(self.biomes, 3)
        self.gameRegistry.registerDimension(dimensionHandler)

        # Register the events
        self.gameRegistry.registerEventHandler(onTick, 'onTick')
        self.gameRegistry.registerEventHandler(onDisconnect, 'onDisconnect')

def onTick(game, tick):
    if tick%5 == 0:
        # Send server updates to all of the connected clients 6 times a second
        return
        game.getModInstance('ServerMod').packetPipeline.sendToAll(WorldUpdatePacket(game.world))

class KickPlayerCommand(cmd.Command):
    def run(self, username, *args):
        pp = self.game.getModInstance('ServerMod').packetPipeline
        # Send a failure message if the user doesn't have elevated privileges
        if username not in open('mods/default/server/elevated_users').read().split('\n')[:-1]:
            pp.sendToPlayer(SendCommandPacket('/message You do not have permission to use that command'), username)
            return

        for player in args:
            # Loop the players, and kick them by deleting the PacketHandler
            for p in self.game.world.players:
                # Kick the player if they match
                if player == p.username:
                    pp.sendToPlayer(DisconnectPacket('You have been kicked from the server.'), p.username)
                    break

def onDisconnect(game):
    '''
    Event Hook: onDisconnect
    Print a little message in the server console
    '''
    print('A Client has disconnected')
