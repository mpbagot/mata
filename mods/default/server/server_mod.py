# Import the API modules
from mod import Mod
from api import network, biome, cmd, dimension, entity, item, properties, vehicle
from api.packets import *

# Import the extra mod data
from mods.default.packets import *
import util

class ServerMod(Mod):
    modName = 'ServerMod'

    def preLoad(self):
        pass

    def load(self):
        # Initialise the packet pipeline
        self.packetPipeline = network.PacketHandler(self.game, util.SERVER)
        # Register the valid packet classes
        self.packetPipeline.registerPacket(ByteSizePacket)
        self.packetPipeline.registerPacket(LoginPacket)
        self.packetPipeline.registerPacket(SendWorldPacket)
        self.packetPipeline.registerPacket(WorldUpdatePacket)
        self.packetPipeline.registerPacket(ConfirmPacket)
        self.packetPipeline.registerPacket(DisconnectPacket)
        # Register the packet handler with the game
        self.gameRegistry.registerPacketHandler(self.packetPipeline)

    def postLoad(self):
        # Register the commands
        self.commands = [('/kick', KickPlayerCommand)]
        for comm in self.commands:
            self.gameRegistry.registerCommand(*comm)

        # Register the biomes
        self.biomes = []
        dimensionHandler = dimension.DimensionHandler(self.biomes, 30)
        self.gameRegistry.registerDimension(dimensionHandler)

        self.gameRegistry.registerEventHandler(onTick, 'onTick')

def onTick(game):
    # Send server updates to all of the connected clients
    if not game.world.isGenerating:
        # game.getModInstance('ServerMod').packetPipeline.sendToAll(WorldUpdatePacket(game.world))
        pass

class KickPlayerCommand(cmd.Command):
    def run(self, *args):
        for player in args:
            # Loop the players, and kick them by deleting the PacketHandler
            for p in self.game.world.players:
                # kick the player if they match
                if player.username == p:
                    self.getModInstance('ServerMod').packetPipeline.sendToPlayer(
                                DisconnectPacket('You have been kicked from the server.'),
                                                                               p.username)
