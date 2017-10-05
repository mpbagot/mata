# Import the API modules
from mod import Mod
from api import audio, network, biome, cmd, dimension, entity, gui, item, properties, vehicle
# Import the extra mod data
from mods.default.packets import *
import util

class ServerMod(Mod):
    def initialiseProperties(self):
        '''
        Initialise the name of the mod
        '''
        self.modName = 'ServerMod'

    def preLoad(self):
        # Register the biomes
        dimensionHandler = dimension.DimensionHandler(self.biomes, 30)
        self.gameRegistry.registerDimension(dimensionHandler)
        pass

    def load(self):
        # Initialise the packet pipeline
        self.packetPipeline = network.PacketHandler(util.SERVER)
        # Register the valid packet classes
        self.packetPipeline.registerPacket(ByteSizePacket)
        self.packetPipeline.registerPacket(LoginPacket)
        self.packetPipeline.registerPacket(WorldUpdatePacket)
        self.packetPipeline.registerPacket(ConfirmPacket)
        self.packetPipeline.registerPacket(DisconnectPacket)
        # Register the packet handler with the game
        self.gameRegistry.registerPacketHandler(self.packetPipeline)

    def postLoad(self):
        # Register the commands
        self.commands = [KickPlayerCommand('/kick', self.worldProperties)]
        for comm in self.commands:
            self.gameRegistry.registerCommand(comm)

class KickPlayerCommand(cmd.Command):
    def run(self, *args):
        for player in args:
            # Loop the players, and kick them by deleting the PacketHandler
            worldPlayers = self.world.properties['players']
            for p in worldPlayers:
                # TODO kick the player if they match
                pass
