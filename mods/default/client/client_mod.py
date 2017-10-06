from mod import Mod
from api import audio, network, biome, cmd, dimension, entity, gui, item, properties, vehicle

from mods.default.packets import *
from mods.default.client.client_gui import *
import util

import pygame
pygame.init()

class ClientMod(Mod):
    modName = 'ClientMod'

    def preLoad(self):
        # Initialise the display and throw a loading image on it for now
        pygame.display.set_mode((1024, 768))
        img = pygame.image.load('resources/textures/load.png').convert()
        pygame.display.get_surface().blit(img, [0, 0])
        pygame.display.flip()

    def load(self):
        # Initialise the packet pipeline
        self.packetPipeline = network.PacketHandler(util.CLIENT)
        # Register the valid packet classes
        self.packetPipeline.registerPacket(ByteSizePacket)
        self.packetPipeline.registerPacket(LoginPacket)
        self.packetPipeline.registerPacket(WorldUpdatePacket)
        self.packetPipeline.registerPacket(ConfirmPacket)
        self.packetPipeline.registerPacket(DisconnectPacket)
        # Register the packet handler with the game
        self.gameRegistry.registerPacketHandler(self.packetPipeline)

    def postLoad(self):
        self.disconnectMessageGui = self.gameRegistry.registerGUI(DisconnectMessage)
        pass
