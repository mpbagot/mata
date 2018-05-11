from mod import Mod
from api import audio, network, cmd, dimension, item, properties, vehicle
from api.packets import *
from api.colour import hueShiftImage

from mods.default.packets import *
from mods.default.biomes import *
from mods.default.items import *
from mods.default.dimension import DefaultChunkProvider
from mods.default.client.gui.game_screens import *
from mods.default.client.gui.game_overlays import *
from mods.default.client.gui.messages import *
from mods.default.client.events import tick_events, other_events
from mods.default.server.entity import bear, npc
from mods.default.server.vehicle import horse

import util

import pygame

class ClientMod(Mod):
    modName = 'ClientMod'

    def preLoad(self):
        self.oldPlayerPos = [0, 0]
        self.genLock = False
        self.chatMessages = {"global" : [], "faction" : []}
        self.latestChatTabs = []

        self.worldUpdateProperty = properties.Property(newPos=[0, 0], updateTick=0)

        # Initialise the display
        pygame.display.set_mode((1024, 768), util.DISPLAY_FLAGS)
        pygame.display.set_caption('M.A.T.A: Medieval Attack-Trade-Alliance')
        # pygame.display.set_icon(pygame.image.load('resources/textures/icon.png').convert_alpha())

        # Register the tile images
        images = ['gravel', 'grass', 'dirt', 'road', 'sand', 'water']
        for i in images:
            img = pygame.image.load('resources/textures/mods/tiles/' + i + '.png').convert()
            self.gameRegistry.registerResource('tile_' + i, img)

        # Register the entity images
        images = ['bear']
        for i in images:
            img = pygame.image.load('resources/textures/mods/entity/' + i + '.png').convert_alpha()
            self.gameRegistry.registerResource('entity_' + i, img)

        # Register the vehicle images
        images = ['horse']
        for i in images:
            img = pygame.image.load('resources/textures/mods/entity/' + i + '.png').convert_alpha()
            self.gameRegistry.registerResource('vehicle_' + i, img)

        # Register weapon images
        images = []#'steel_sword']
        for i in images:
            img = pygame.image.load('resources/textures/mods/items/' + i + '.png').convert_alpha()
            self.gameRegistry.registerResource('weapon_' + i, img)

        # Register item images
        images = []#'gold']
        for i in images:
            img = pygame.image.load('resources/textures/mods/items/' + i + '.png').convert_alpha()
            self.gameRegistry.registerResource('item_' + i, img)

    def load(self):
        # Initialise the packet pipeline
        self.packetPipeline = network.PacketHandler(self.game, util.CLIENT, self.game.getOpenPort())

        # Register the valid packet classes
        packets = [
                    FetchPlayerImagePacket, SendInventoryPacket,
                    FetchInventoryPacket, SendPlayerImagePacket,
                    FetchPickupItem, SendPickupItem,
                    StartTradePacket, ConfirmTradePacket,
                    EndTradePacket, RespondTradePacket
                  ]
        for packet in packets:
            self.packetPipeline.registerPacket(packet)

        # Register the packet handler with the game
        self.gameRegistry.registerPacketHandler(self.packetPipeline)

        # Initialise the GUI's
        self.gameGui = self.gameRegistry.registerGUI(GameScreen)
        self.playerDrawGui = self.gameRegistry.registerGUI(PlayerDrawScreen)
        self.loadingGui = self.gameRegistry.registerGUI(LoadingScreen)
        self.enteringGui = self.gameRegistry.registerGUI(DimLoadingScreen)
        self.mainMenuGui = self.gameRegistry.registerGUI(MainMenu)
        self.inventoryGui = self.gameRegistry.registerGUI(PlayerInventoryScreen)
        self.tradeGui = self.gameRegistry.registerGUI(TradeScreen)
        self.disconnectMessageGui = self.gameRegistry.registerGUI(DisconnectMessage)

        # Initialise the Overlays
        self.hudOverlay = self.gameRegistry.registerGUI(HUD)
        self.chatOverlay = self.gameRegistry.registerGUI(Chat)
        self.pauseOverlay = self.gameRegistry.registerGUI(Pause)

        # Register the entities
        self.gameRegistry.registerEntity(bear.Bear())
        self.gameRegistry.registerEntity(npc.NPC())
        self.gameRegistry.registerVehicle(horse.Horse())

        # Register the items
        self.gameRegistry.registerItem(Dirt)
        self.gameRegistry.registerItem(Sword)
        self.gameRegistry.registerItem(Gold)

    def postLoad(self):
        # Open the main menu on startup
        self.game.openGui(self.mainMenuGui)

        # Initialise the biomes
        self.biomes = [Ocean, Forest, City, Desert]
        # Initialise and register the DimensionHandler accordingly
        dimensionHandler = dimension.DimensionHandler(DefaultChunkProvider(self.biomes, 3), dimension.WorldMP())
        self.gameRegistry.registerDimension(dimensionHandler)

        # Register the events
        self.gameRegistry.registerEventHandler(tick_events.onTickGenerateWorld, 'onTick')
        self.gameRegistry.registerEventHandler(tick_events.onTickHandleMovement, 'onTick')
        self.gameRegistry.registerEventHandler(tick_events.onTickSyncPlayer, 'onTick')

        self.gameRegistry.registerEventHandler(other_events.onPlayerLogin, 'onPlayerLogin')
        self.gameRegistry.registerEventHandler(other_events.onCommand, 'onCommand')
        self.gameRegistry.registerEventHandler(other_events.onPacketReceived, 'onPacketReceived')
        self.gameRegistry.registerEventHandler(other_events.onPlayerSync, 'onPlayerSync')
        self.gameRegistry.registerEventHandler(other_events.onEntitySync, 'onEntitySync')
        self.gameRegistry.registerEventHandler(other_events.onVehicleSync, 'onVehicleSync')
        self.gameRegistry.registerEventHandler(other_events.onDimensionChange, 'onDimensionChange')
        self.gameRegistry.registerEventHandler(other_events.onDisconnect, 'onDisconnect')

        self.gameRegistry.registerEventHandler(other_events.onGameMouseClick, 'onMouseClick')
        self.gameRegistry.registerEventHandler(other_events.onInvMouseClick, 'onMouseClick')

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
