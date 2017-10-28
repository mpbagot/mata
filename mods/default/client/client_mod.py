from mod import Mod
from api import audio, network, biome, cmd, dimension, entity, gui, item, properties, vehicle
from api.packets import *

from mods.default.packets import *
from mods.default.biomes import *
from mods.default.client.client_gui import *
import util

from threading import Thread
from copy import deepcopy

class ClientMod(Mod):
    modName = 'ClientMod'

    def preLoad(self):
        self.oldPlayerPos = [0, 0]
        self.readyToStart = False

        self.relPos2Property = properties.Property(pos=[0, 0], ready=False)

        # Initialise the display
        pygame.display.set_mode((1024, 768))
        pygame.display.set_caption('A Game')
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
        self.gameRegistry.registerEventHandler(onTick, 'onTick')
        self.gameRegistry.registerEventHandler(onClientConnected, 'onClientConnected')
        self.gameRegistry.registerEventHandler(onPlayerLogin, 'onPlayerLogin')
        self.gameRegistry.registerEventHandler(onPacketReceived, 'onPacketReceived')
        self.gameRegistry.registerEventHandler(onDisconnect, 'onDisconnect')

    def generateLargePlayerImage(self, hueTransforms):
        imageData = []
        if hueTransforms == None:
            return imageData
        return []

    def calculateAvatar(self, hueTransforms):
        imageData = []
        if hueTransforms == None:
            return imageData
        return []

def onPacketReceived(game, packet):
    if packet.__class__.__name__ == 'DisconnectPacket':
        # Open a GUI that displays the message, and disconnect them
        game.openGui(game.getModInstance('ClientMod').disconnectMessageGui, packet.message)
    elif packet.__class__.__name__ == 'ResetPlayerPacket':
        # Tell the game that the player is synced
        game.player.synced = True
    elif packet.__class__.__name__ == 'InvalidLoginPacket':
        # Tell the player that their username is already taken
        game.openGui(game.getModInstance('ClientMod').mainMenuGui)
        game.openGUI.error = 'That Username Is Already Taken.'
    elif packet.__class__.__name__ == 'WorldUpdatePacket':
        # Fetch images of new players
        for p, player in enumerate(game.world.players):
            if player.img == None:
                game.getModInstance('ClientMod').packetPipeline.sendToServer(FetchPlayerImagePacket(player))

def onDisconnect(game):
    game.openGui(game.getModInstance('ClientMod').disconnectMessageGui, 'Server Connection Reset')

def onClientConnected(game):
    print('connection to server established')
    game.player.setProperty('relPos2', game.getModInstance('ClientMod').relPos2Property)

def onPlayerLogin(game, player):
    # Show the player customisation screen
    game.openGui(game.getModInstance('ClientMod').playerDrawGui, game)

def onTick(game, tick):
    # Check if this client has connected to a server
    if game.getModInstance('ClientMod').packetPipeline.connections:
        # Sync player data back to the server periodically
        if tick%3 == 0:
            # Check if the player has moved
            if game.player.relPos != game.getModInstance('ClientMod').oldPlayerPos:
                game.player.synced = False
                # Duplicate the player and set the position
                playerCopy = deepcopy(game.player)
                playerCopy.pos = list(game.player.getAbsPos())
                # Store the current relative position in the mod instance for later comparison
                game.getModInstance('ClientMod').oldPlayerPos = list(game.player.relPos)
                # Send the copy of the player object in the packet
                game.getModInstance('ClientMod').packetPipeline.sendToServer(SyncPlayerPacket(playerCopy))

        # Handle player movement
        keys = pygame.key.get_pressed()
        speed = 0.2

        # Update the secondary relative position
        props = game.player.getProperty('relPos2')
        if props.props['ready']:
            if keys[pygame.K_UP]:
                props.props['pos'][1] -= speed
            if keys[pygame.K_DOWN]:
                props.props['pos'][1] += speed
            if keys[pygame.K_LEFT]:
                props.props['pos'][0] -= speed
            if keys[pygame.K_RIGHT]:
                props.props['pos'][0] += speed
            game.player.setProperty('relPos2', props)

        # Update the relative position
        if keys[pygame.K_UP]:
            game.player.relPos[1] -= speed
        if keys[pygame.K_DOWN]:
            game.player.relPos[1] += speed
        if keys[pygame.K_LEFT]:
            game.player.relPos[0] -= speed
        if keys[pygame.K_RIGHT]:
            game.player.relPos[0] += speed

        # If the player has moved more than a certain distance, generate the world
        absRelPos = [abs(a) for a in game.player.relPos]
        if (game.player.synced and not game.world.world) or max(absRelPos) > 26:
            # Set the second relative position to start iterating
            props = game.player.getProperty('relPos2')

            # Generate the world on the client
            t = Thread(target=genWorld, args=(game, props))
            t.daemon = True
            t.start()

def genWorld(game, props):
    if props.props['ready'] == True:
        return
    # Set the abs pos of the player
    preGenPos = game.player.getAbsPos()
    print('genning world')
    props.props['ready'] = True
    game.player.setProperty('relPos2', props)

    # Generate the world
    world = game.modLoader.gameRegistry.dimensions[game.player.dimension].getWorldObj()
    worldData = world.generate(preGenPos, game.modLoader.gameRegistry).world.map
    game.world.world.map = worldData
    print('world gen done')

    # Fetch the player property
    props = game.player.getProperty('relPos2')

    # Move the player
    game.player.pos = preGenPos
    game.player.relPos = list(props.props['pos'])

    # Update the player property
    props.props['ready'] = False
    props.props['pos'] = [0, 0]

    # Set the property back into the player
    game.player.setProperty('relPos2', props)
