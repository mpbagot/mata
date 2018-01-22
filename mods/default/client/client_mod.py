from mod import Mod
from api import audio, network, biome, cmd, dimension, entity, gui, item, properties, vehicle
from api.packets import *
from api.colour import HueShifter, hueShiftImage

from mods.default.packets import *
from mods.default.biomes import *
from mods.default.client.client_gui import *
from mods.default.client.events import tick_events, other_events
from mods.default.server.entity import bear

import util

import pygame

class ClientMod(Mod):
    modName = 'ClientMod'

    def preLoad(self):
        self.oldPlayerPos = [0, 0]
        self.readyToStart = False
        self.chatMessages = {"global" : [], "faction" : []}

        self.relPos2Property = properties.Property(pos=[0, 0], ready=False)
        self.worldUpdateProperty = properties.Property(newPos=[0, 0], updateTick=0)

        # Initialise the display
        pygame.display.set_mode((1024, 768))#, pygame.FULLSCREEN)
        pygame.display.set_caption('M.A.T.A: Medieval Attack-Trade-Alliance')
        # pygame.display.set_icon(pygame.image.load('resources/textures/icon.png').convert_alpha())

        images = ['gravel', 'grass', 'dirt', 'road', 'sand', 'water']
        for i in images:
            img = pygame.image.load('resources/textures/mods/tiles/'+i+'.png').convert()
            self.gameRegistry.registerResource('tile_'+i, img)

        images = ['bear']
        for i in images:
            img = pygame.image.load('resources/textures/mods/entity/'+i+'.png').convert_alpha()
            self.gameRegistry.registerResource('entity_'+i, img)

    def load(self):
        # Initialise the packet pipeline
        self.packetPipeline = network.PacketHandler(self.game, util.CLIENT)

        # Register the valid packet classes
        self.packetPipeline.registerPacket(WorldUpdatePacket)
        self.packetPipeline.registerPacket(SendInventoryPacket)
        self.packetPipeline.registerPacket(FetchInventoryPacket)
        self.packetPipeline.registerPacket(SendPlayerImagePacket)
        self.packetPipeline.registerPacket(FetchPlayerImagePacket)

        # Register the packet handler with the game
        self.gameRegistry.registerPacketHandler(self.packetPipeline)

        # Initialise the GUI's
        self.gameGui = self.gameRegistry.registerGUI(GameScreen)
        self.playerDrawGui = self.gameRegistry.registerGUI(PlayerDrawScreen)
        self.loadingGui = self.gameRegistry.registerGUI(LoadingScreen)
        self.mainMenuGui = self.gameRegistry.registerGUI(MainMenu)
        self.inventoryGui = self.gameRegistry.registerGUI(PlayerInventoryScreen)
        self.disconnectMessageGui = self.gameRegistry.registerGUI(DisconnectMessage)

        # Initialise the Overlays
        self.hudOverlay = self.gameRegistry.registerGUI(HUD)
        self.chatOverlay = self.gameRegistry.registerGUI(Chat)

        # Register the entities
        self.gameRegistry.registerEntity(bear.Bear())

    def postLoad(self):
        # Open the main menu on startup
        self.game.openGui(self.mainMenuGui)

        # Register the message override command
        self.gameRegistry.registerCommand('/message', MessageCommand)

        # Initialise the biomes
        self.biomes = [Ocean, Forest, City, Desert]
        # Initialise and register the DimensionHandler accordingly
        dimensionHandler = dimension.DimensionHandler(self.biomes, 3)
        self.gameRegistry.registerDimension(dimensionHandler)

        # Register the events
        self.gameRegistry.registerEventHandler(tick_events.onTickGenerateWorld, 'onTick')
        self.gameRegistry.registerEventHandler(tick_events.onTickHandleMovement, 'onTick')
        self.gameRegistry.registerEventHandler(tick_events.onTickSyncPlayer, 'onTick')

        self.gameRegistry.registerEventHandler(other_events.onClientConnected, 'onClientConnected')
        self.gameRegistry.registerEventHandler(other_events.onPlayerLogin, 'onPlayerLogin')
        self.gameRegistry.registerEventHandler(other_events.onPacketReceived, 'onPacketReceived')
        self.gameRegistry.registerEventHandler(other_events.onDisconnect, 'onDisconnect')
        self.gameRegistry.registerEventHandler(other_events.onPlayerUpdate, 'onPlayerUpdate')
        self.gameRegistry.registerEventHandler(other_events.onEntitySync, 'onEntitySync')

        self.gameRegistry.registerEventHandler(other_events.onGameKeyPress, 'onKeyPress')
        self.gameRegistry.registerEventHandler(other_events.onInvKeyPress, 'onKeyPress')

    def generateLargePlayerImage(self, imgValues):
        '''
        Generate the large player image using an array of hue shift values
        '''
        # Initialise the surface and the image data
        image = pygame.Surface((75, 132)).convert_alpha()
        # Return a hueshifted version of the image
        return hueShiftImage(imgValues, 'player_img', image)

    def calculateAvatar(self, imgValues):
        '''
        Generate the in-world player avatar using an array of hue shift values
        '''
        image = pygame.Surface((40, 40)).convert_alpha()
        imageNames = ['player_avatar_{}'.format(a) for a in range(4)]
        # Generate 4 frames per player, 3 frames per direction
        # Filename is player_avatar_<direction_id>_<frame_id>_<characteristic_id>_<type_id>.png
        # Direction is between 0-3, frame is between 0-2, characteristic is between 0-6, type is between 0-5
        # return [[self.hueShiftImage(imgValues, imageName+'_'+str(a), image) for a in range(3)] for imageName in imageNames]
        return hueShiftImage(imgValues, 'player_avatar_0', image)

class MessageCommand(cmd.Command):
    def run(self, username, *args):
        message = ' '.join(args[1:])
        modInstance = self.game.getModInstance('ClientMod')
        modInstance.chatMessages[args[0]] = modInstance.chatMessages.get(args[0], []) + [message]
        print(' '.join(args[1:]))
