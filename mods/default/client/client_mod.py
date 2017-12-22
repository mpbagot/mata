from mod import Mod
from api import audio, network, biome, cmd, dimension, entity, gui, item, properties, vehicle
from api.packets import *
from api.colour import HueShifter, hueShiftImage

from mods.default.packets import *
from mods.default.biomes import *
from mods.default.client.client_gui import *
from mods.default.client.events import tick_events
import util

import pygame

class ClientMod(Mod):
    modName = 'ClientMod'

    def preLoad(self):
        self.oldPlayerPos = [0, 0]
        self.readyToStart = False

        self.relPos2Property = properties.Property(pos=[0, 0], ready=False)
        self.worldUpdateProperty = properties.Property(newPos=[0, 0], updateTick=0)

        # Initialise the display
        pygame.display.set_mode((1024, 768), pygame.FULLSCREEN)
        pygame.display.set_caption('M.A.T.A: Medieval Attack-Trade-Alliance')
        # pygame.display.set_icon(pygame.image.load('resources/textures/icon.png').convert_alpha())

        images = ['gravel', 'grass', 'dirt', 'road', 'sand', 'water']
        for i in images:
            img = pygame.image.load('resources/textures/mods/tiles/'+i+'.png')
            self.gameRegistry.registerResource('tile_'+i, img)

    def load(self):
        # Initialise the packet pipeline
        self.packetPipeline = network.PacketHandler(self.game, util.CLIENT)
        # Register the valid packet classes
        self.packetPipeline.registerPacket(WorldUpdatePacket)
        self.packetPipeline.registerPacket(SendPlayerImagePacket)
        self.packetPipeline.registerPacket(FetchPlayerImagePacket)
        # Register the packet handler with the game
        self.gameRegistry.registerPacketHandler(self.packetPipeline)

        # Initialise the GUI's
        self.gameGui = self.gameRegistry.registerGUI(GameScreen)
        self.playerDrawGui = self.gameRegistry.registerGUI(PlayerDrawScreen)
        self.loadingGui = self.gameRegistry.registerGUI(LoadingScreen)
        self.mainMenuGui = self.gameRegistry.registerGUI(MainMenu)
        self.disconnectMessageGui = self.gameRegistry.registerGUI(DisconnectMessage)

        # Initialise the Overlays
        self.hudOverlay = self.gameRegistry.registerGUI(HUD)

    def postLoad(self):
        # Open the main menu on startup
        self.game.openGui(self.mainMenuGui)

        # Initialise the biomes
        self.biomes = [Ocean, Forest, City, Desert]
        # Initialise and register the DimensionHandler accordingly
        dimensionHandler = dimension.DimensionHandler(self.biomes, 3)
        self.gameRegistry.registerDimension(dimensionHandler)

        # Register the events
        self.gameRegistry.registerEventHandler(tick_events.onTickGenerateWorld, 'onTick')
        self.gameRegistry.registerEventHandler(tick_events.onTickHandleMovement, 'onTick')
        self.gameRegistry.registerEventHandler(tick_events.onTickSyncPlayer, 'onTick')

        self.gameRegistry.registerEventHandler(onClientConnected, 'onClientConnected')
        self.gameRegistry.registerEventHandler(onPlayerLogin, 'onPlayerLogin')
        self.gameRegistry.registerEventHandler(onPacketReceived, 'onPacketReceived')
        self.gameRegistry.registerEventHandler(onDisconnect, 'onDisconnect')
        self.gameRegistry.registerEventHandler(onPlayerUpdate, 'onPlayerUpdate')

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

def onPacketReceived(game, packet):
    '''
    Event Hook: onPacketReceived
    Hook additional behaviour into the vanilla API packets
    '''
    if packet.__class__.__name__ == 'DisconnectPacket':
        # Open a GUI that displays the message, and disconnect them
        game.openGui(game.getModInstance('ClientMod').disconnectMessageGui, packet.message)

    elif packet.__class__.__name__ == 'ResetPlayerPacket':
        # Tell the game that the player is synced
        game.player.synced = True

    elif packet.__class__.__name__ == 'InvalidLoginPacket':
        # Tell the player that their username is already taken
        game.openGui(game.getModInstance('ClientMod').mainMenuGui)
        game.openGUI[1].error = 'That Username Is Already Taken.'

    elif packet.__class__.__name__ == 'WorldUpdatePacket':
        # Fetch images of new players
        for p, player in enumerate(game.world.players):
            if player.img == None:
                game.getModInstance('ClientMod').packetPipeline.sendToServer(FetchPlayerImagePacket(player))

def onDisconnect(game):
    '''
    Event Hook: onDisconnect
    Handle the opening of the disconnected screen when the client disconnects
    '''
    game.openGui(game.getModInstance('ClientMod').disconnectMessageGui, 'Server Connection Reset')

def onClientConnected(game):
    '''
    Event Hook: onClientConnected
    Apply the extra property to the client player when the connection to the server is established
    '''
    print('connection to server established')
    game.player.setProperty('relPos2', game.getModInstance('ClientMod').relPos2Property)

def onPlayerLogin(game, player):
    '''
    Event Hook: onPlayerLogin
    Open the player customisation screen when the client logs into the server
    '''
    # Show the player customisation screen
    # TODO Change this later
    game.openGui(game.getModInstance('ClientMod').gameGui, game)
    # game.openGui(game.getModInstance('ClientMod').playerDrawGui, game)

def onPlayerUpdate(game, player, oldPlayers):
    '''
    Event Hook: onPlayerUpdate
    Apply the updates to other player attributes from the server
    '''
    # If the player being updated is the client player, skip it
    if player.username == game.player.username:
        return
    for p in range(len(oldPlayers)):
        if oldPlayers[p].username == player.username:
            # Update vanilla player properties
            oldPlayers[p].health = player.health

            # Update the modded properties
            props = oldPlayers[p].getProperty('worldUpdate')
            props.props['newPos'] = player.pos
            props.props['updateTick'] = game.tick
            oldPlayers[p].setProperty('worldUpdate', props)

            return

    player.setProperty('worldUpdate', game.getModInstance('ClientMod').worldUpdateProperty)
    oldPlayers.append(player)
