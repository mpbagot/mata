from mod import Mod
from api import audio, network, biome, cmd, dimension, entity, gui, item, properties, vehicle
from api.packets import *

from mods.default.packets import *
from mods.default.biomes import *
from mods.default.client.client_gui import *
import util


class ClientMod(Mod):
    modName = 'ClientMod'

    def preLoad(self):
        self.oldPlayerPos = [0, 0]
        self.requestMade = False
        self.buffer = []

        self.relPos2Property = properties.Property(pos=[0, 0])

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
        self.gameRegistry.registerEventHandler(onGameLoad, 'onGameLoad')
        self.gameRegistry.registerEventHandler(onPacketReceived, 'onPacketReceived')
        self.gameRegistry.registerEventHandler(onDisconnect, 'onDisconnect')
        self.gameRegistry.registerEventHandler(onPlayerLogin, 'onPlayerLogin')

def onPlayerLogin(game, player):
    player.properties['relPos2'] = game.getModInstance('ClientMod').relPos2Property

def onPacketReceived(game, packet):
    if packet.__class__.__name__ == 'SendWorldPacket':
        if packet.part == 1:
            # game.getModInstance('ClientMod').buffer = [[] for a in range(packet.length)]
            game.getModInstance('ClientMod').buffer = packet.tiles.map
        else:
            game.getModInstance('ClientMod').buffer += packet.tiles.map
        if packet.part == packet.length:
            print('Loading world load buffer into Game')
            game.world.world.map = game.getModInstance('ClientMod').buffer
            # Set the player position and reset the property
            props = game.player.getProperty('relPos2')
            # TODO Move the absolute position of the player
            # TODO Why does this not work?
            # TODO The position doesn't set to the absolute position correctly for some reason
            # TODO It simply resets to the original position, before the player even begins moving
            print('relPos:', game.player.relPos, 'relPos2:', props.props['pos'])
            game.player.pos = game.player.getAbsPos()
            game.player.pos[0] -= props.props['pos'][0]
            game.player.pos[1] -= props.props['pos'][1]
            print(game.player.pos)
            # Set the relative position
            game.player.relPos = props.props['pos']
            # Clear the player property
            props.props['pos'] = [0, 0]
            game.player.setProperty('relPos2', props)
        game.getModInstance('ClientMod').requestMade = False

    elif packet.__class__.__name__ == 'DisconnectPacket':
        # Open a GUI that displays the message, and disconnect them
        game.openGui(game.getModInstance('ClientMod').disconnectMessageGui, packet.message)

def onDisconnect(game):
    game.openGui(game.getModInstance('ClientMod').disconnectMessageGui, 'Server Connection Reset')

def onGameLoad(game):
    game.openGui(game.getModInstance('ClientMod').gameGui, game)

def onTick(game):
    # Sync player data back to the server
    if game.getModInstance('ClientMod').packetPipeline.connections:
        if pygame.time.get_ticks()%100 < 20:
            # Check if the player has moved
            if game.player.relPos != game.getModInstance('ClientMod').oldPlayerPos:
                # Duplicate the player and set the position
                playerCopy = game.player
                playerCopy.pos = game.player.getAbsPos()
                # Store the current relative position in the mod instance for later comparison
                game.getModInstance('ClientMod').oldPlayerPos = game.player.relPos
                # Send the copy of the player object in the packet
                game.getModInstance('ClientMod').packetPipeline.sendToServer(SyncPlayerPacketServer(playerCopy))

    # If the player has moved more than a certain distance, fetch the world data
    # print(game.player.pos)
    absRelPos = [abs(a) for a in game.player.relPos]
    if max(absRelPos) > 26 and not game.getModInstance('ClientMod').requestMade:
        absPos = game.player.getAbsPos()
        print(game.player.getAbsPos())
        game.getModInstance('ClientMod').packetPipeline.sendToServer(RequestWorldPacket(game.player.dimension, absPos))
        game.getModInstance('ClientMod').requestMade = True

    # Handle player movement
    keys = pygame.key.get_pressed()
    speed = 0.1
    if game.getModInstance('ClientMod').requestMade:
        print('here')
        # Fetch the Entity Property
        relPos2 = game.player.getProperty('relPos2')
        # Update it
        if keys[pygame.K_UP]:
            relPos2.props['pos'][1] -= speed
        if keys[pygame.K_DOWN]:
            relPos2.props['pos'][1] += speed
        if keys[pygame.K_LEFT]:
            relPos2.props['pos'][0] -= speed
        if keys[pygame.K_RIGHT]:
            relPos2.props['pos'][0] += speed
        # Store it back in
        game.player.setProperty('relPos2', relPos2)

    if keys[pygame.K_UP]:
        game.player.relPos[1] -= speed
    if keys[pygame.K_DOWN]:
        game.player.relPos[1] += speed
    if keys[pygame.K_LEFT]:
        game.player.relPos[0] -= speed
    if keys[pygame.K_RIGHT]:
        game.player.relPos[0] += speed
