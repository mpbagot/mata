from mod import Mod
from api import audio, network, biome, cmd, dimension, entity, gui, item, properties, vehicle
from api.packets import *

from mods.default.packets import *
from mods.default.client.client_gui import *
import util

import pygame
pygame.init()

class ClientMod(Mod):
    modName = 'ClientMod'

    def preLoad(self):
        # Initialise the display
        pygame.display.set_mode((1024, 768))

    def load(self):
        # Initialise the packet pipeline
        self.packetPipeline = network.PacketHandler(self.game, util.CLIENT)
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
        self.gameGui = self.gameRegistry.registerGUI(GameScreen)
        self.loadingGui = self.gameRegistry.registerGUI(LoadingScreen)
        self.mainMenuGui = self.gameRegistry.registerGUI(MainMenu)
        self.disconnectMessageGui = self.gameRegistry.registerGUI(DisconnectMessage)
