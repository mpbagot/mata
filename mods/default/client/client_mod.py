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

    def load(self):
        # Initialise the packet pipeline
        self.packetPipeline = network.PacketHandler(self.game, util.CLIENT)
        # Register the valid packet classes
        self.packetPipeline.registerPacket(WorldUpdatePacket)
        # Register the packet handler with the game
        self.gameRegistry.registerPacketHandler(self.packetPipeline)

    def postLoad(self):
        # Initialise the GUI's
        self.gameGui = self.gameRegistry.registerGUI(GameScreen)
        self.loadingGui = self.gameRegistry.registerGUI(LoadingScreen)
        self.mainMenuGui = self.gameRegistry.registerGUI(MainMenu)
        self.disconnectMessageGui = self.gameRegistry.registerGUI(DisconnectMessage)

        # Open the main menu on startup
        self.game.openGui(self.mainMenuGui)

        # Initialise the biomes
        self.biomes = [Ocean, Forest, City, Desert]
        # Initialise and register the DimensionHandler accordingly
        dimensionHandler = dimension.DimensionHandler(self.biomes, 3)
        self.gameRegistry.registerDimension(dimensionHandler)

        # Register the events
        self.gameRegistry.registerEventHandler(onTick, 'onTick')
        self.gameRegistry.registerEventHandler(onPlayerLogin, 'onPlayerLogin')
        self.gameRegistry.registerEventHandler(onPacketReceived, 'onPacketReceived')
        self.gameRegistry.registerEventHandler(onDisconnect, 'onDisconnect')

def onPacketReceived(game, packet):
    if packet.__class__.__name__ == 'DisconnectPacket':
        # Open a GUI that displays the message, and disconnect them
        game.openGui(game.getModInstance('ClientMod').disconnectMessageGui, packet.message)
    elif packet.__class__.__name__ == 'SyncPlayerPacketClient':
        # Tell the game that the player is synced
        game.player.synced = True

def onDisconnect(game):
    game.openGui(game.getModInstance('ClientMod').disconnectMessageGui, 'Server Connection Reset')

def onPlayerLogin(game, player):
    print('player logged in')
    player.setProperty('relPos2', game.getModInstance('ClientMod').relPos2Property)

def onTick(game):
    # Check if the main game is running
    if game.getModInstance('ClientMod').packetPipeline.connections:
        # Sync player data back to the server
        if pygame.time.get_ticks()%100 < 20:
            # Check if the player has moved
            if game.player.relPos != game.getModInstance('ClientMod').oldPlayerPos:
                game.player.synced = False
                # Duplicate the player and set the position
                playerCopy = deepcopy(game.player)
                playerCopy.pos = list(game.player.getAbsPos())
                # Store the current relative position in the mod instance for later comparison
                game.getModInstance('ClientMod').oldPlayerPos = list(game.player.relPos)
                # Send the copy of the player object in the packet
                game.getModInstance('ClientMod').packetPipeline.sendToServer(SyncPlayerPacketServer(playerCopy))

        # Handle player movement
        keys = pygame.key.get_pressed()
        speed = 0.2

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
            # Generate the world on the client
            t = Thread(target=genWorld, args=(game, props))
            t.daemon = True
            t.start()

            # Set the second relative position to start iterating
            props = game.player.getProperty('relPos2')
            props.props['ready'] = True
            game.player.setProperty('relPos2', props)

def genWorld(game, props):
    if props.props['ready'] == True:
        return
    # Set the abs pos of the player
    preGenPos = game.player.getAbsPos()
    # Generate the world
    world = game.modLoader.gameRegistry.dimensions[game.player.dimension].getWorldObj()
    worldData = world.generate(preGenPos).world.map
    game.world.world.map = worldData
    print('world gen done')

    # Move the player
    # print(game.player.getAbsPos())
    game.player.pos = preGenPos
    game.player.relPos = list(props.props['pos'])

    props = game.player.getProperty('relPos2')
    props.props['ready'] = False
    props.props['pos'] = [0, 0]
    game.player.setProperty('relPos2', props)

    # Show the game screen
    game.openGui(game.getModInstance('ClientMod').gameGui, game)
