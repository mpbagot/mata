'''
game.py
A module containing the main game object/class
'''

# Import the standard libraries
import time
import multiprocessing
import pygame.mouse

# Import the game's modules
import util
import mods.default.client.client_mod as client
import mods.default.server.server_mod as server
import mods.default.neural_net as nn

class Game:
    '''
    A class to hold all of the elements of the game together
    '''
    def __init__(self, modLoader, argHandler):
        self.modLoader = modLoader
        self.processCommandLineArgs(argHandler)
        self.args = argHandler
        self.world = None
        self.openGUI = None
        self.openOverlays = []

        # Load all of the registered mods
        self.modLoader.loadRegisteredMods()

        # Check if this works
        if self.args.getRuntimeType() != util.SERVER:
            self.openGui(0, 'You have been disconnected!')

        # Set the world up
        if self.args.getRuntimeType() == util.SERVER:
            self.world = self.modLoader.gameRegistry.getWorld()

    def run(self):
        '''
        Run the game after initialising all of the mods
        '''
        # Run at 30 ticks per second
        while True:
            # Get the start time of the tick
            startTickTime = time.time()
            # Run all updates that occur in a tick here
            if self.world and self.args.getRuntimeType() == util.SERVER:
                self.world.tickUpdate(self)
            # Trigger all of the onTick events
            for func in self.modLoader.gameRegistry.eventFunctions.get('onTick', []):
                func(self)

            # Draw the client game
            if self.args.getRuntimeType() != util.SERVER:
                self.drawClientGame()

            # Get the time that the tick took to run
            deltaTime = time.time()-startTickTime
            # Sleep if running faster than 30 ticks per second
            if deltaTime < 1/30:
                time.sleep((1/30)-deltaTime)

    def drawClientGame(self):
        '''
        Draw the game to the pygame display
        '''
        pygame.display.get_surface().fill((255, 255, 255))

        # Grab the mouse position
        pos = pygame.mouse.get_pos()
        # Draw the current gui
        if self.openGUI is not None:
            self.openGUI[1].drawBackgroundLayer()
            self.openGUI[1].drawMiddleLayer(pos)
            self.openGUI[1].drawForegroundLayer(pos)

        # Draw each of the active overlays
        for id, overlay in self.openOverlays:
            overlay.drawBackgroundLayer()
        for id, overlay in self.openOverlays:
            overlay.drawMiddleLayer(pos)
        for id, overlay in self.openOverlays:
            overlay.drawForegroundLayer(pos)

        # Draw the graphics to the screen
        pygame.display.flip()

    def openGui(self, guiID, *args):
        '''
        Open the GUI with the given id for this client
        '''
        self.openGUI = [guiID, self.modLoader.gameRegistry.guis[guiID](*args)]

    def openOverlay(self, guiID, *args):
        '''
        Add an overlay to be drawn to the screen
        '''
        self.openOverlays.append([guiID, self.modLoader.gameRegistry.guis[guiID](*args)])

    def closeGui(self):
        '''
        Close the currently open gui
        '''
        self.openGui = None

    def closeOverlay(self, guiID):
        '''
        Close the overlay with the given id
        '''
        index = None
        for i, overlay in enumerate(self.openOverlays):
            if overlay[0] == guiID:
                del self.openOverlays[i]
                return
        print('[ERROR] Overlay is not currently open.')

    def processCommandLineArgs(self, argHandler):
        '''
        Process the Command Line Arguments for the game
        '''
        if argHandler.getRuntimeType() == util.SERVER:
            # Schedule the Server side mods to be loaded here
            self.modLoader.registerMod(server.ServerMod)

        elif argHandler.getRuntimeType() in [util.CLIENT, util.COMBINED]:
            if argHandler.getRuntimeType() == util.COMBINED:
                # Fork a new Server process, then set to connect to it immediately
                serverProcess = multiprocessing.Process(target=forkServer)
                serverProcess.daemon = True
                serverProcess.start()
            # Schedule the Client side mods to be loaded here
            self.modLoader.registerMod(client.ClientMod)

        if argHandler.getRunSpecialAI():
            # Schedule the special Neural Network AI mod to be loaded
            self.modLoader.registerMod(nn.NNetAIMod)

        if argHandler.getShouldLoadCustomMods():
            # Schedule the loading of the extra custom mods ,
            # if they aren't disabled in the command line.
            for modName in open('modlist'):
                self.modLoader.registerModByName(modName)

        # Print a helpful message
        print('Starting Game in {} Mode'.format({util.SERVER : 'SERVER',
                                                 util.CLIENT : 'CLIENT',
                                                 util.COMBINED : 'COMBINED'
                                                }[argHandler.getRuntimeType()]))

def forkServer():
    '''
    Fork a new process to run the server in the background
    '''
    import mod
    serverRuntime = Game(mod.ModLoader(), util.ArgumentHandler(['--type', 'SERVER']))
    serverRuntime.run()
