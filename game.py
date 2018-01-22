'''
game.py
A module containing the main game object/class
'''

# Import the standard libraries
import time
import multiprocessing
import socket
import sys

if 'SERVER' not in sys.argv:
    import pygame
    pygame.init()

# Import the game's modules
import util
import mod
from api.entity import Player

class Game:
    '''
    A class to hold all of the elements of the game together
    '''
    def __init__(self, argHandler):
        # Initialise the child process value
        self.child = None

        # Load mods and process cmd args
        self.modLoader = mod.ModLoader(self)
        self.processCommandLineArgs(argHandler)
        self.args = argHandler

        # Initialise the game variables
        self.world = None
        self.openGUI = self.prevGUI = None
        self.openOverlays = []
        self.prevOverlays = []

        # Load all of the registered mods
        self.modLoader.loadRegisteredMods()

        # Load into the main menu or loading screen gui on startup
        if self.args.getRuntimeType() != util.SERVER:
            self.player = Player()
        # Fill in the address to connect to automatically
        if self.args.getRuntimeType() == util.COMBINED:
            self.openGUI[1].textboxes[-1].text = self.args.getConnectingAddress()

        # Set the world up
        self.world = self.modLoader.gameRegistry.getWorld()

    def quit(self):
        '''
        Safely disconnect all players, unload the mods and quit the game
        '''
        # Terminate the child server process if running a combined game
        if self.child:
            # TODO this doesn't work...
            self.child.terminate()
        pygame.quit()
        sys.exit()

    def run(self):
        '''
        Run the game after initialising all of the mods
        '''
        self.fireEvent('onGameLaunch')
        self.tick = 0
        # Run at 30 ticks per second
        while True:
            self.tick += 1
            # Get the start time of the tick
            startTickTime = time.time()

            # Tick the world object
            if self.world and self.args.getRuntimeType() == util.SERVER:
                self.world.tickUpdate(self)

            # Trigger all of the onTick events
            self.fireEvent('onTick', self.tick)

            # If running a client side game then do some extra things
            if self.args.getRuntimeType() != util.SERVER:
                # Get the mouse position
                pos = pygame.mouse.get_pos()

                # Draw the client game
                self.drawClientGame(pos)

                # Handle the pygame events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.quit()

                    elif event.type == pygame.KEYDOWN:
                        # Handle a keypress on the gui
                        if self.openGUI[1].currentTextBox is not None:
                            self.openGUI[1].textboxes[self.openGUI[1].currentTextBox].doKeyPress(event)
                        else:
                            # If the keypress is not applicable to the gui, revert to the overlays
                            for i, overlay in enumerate(self.openOverlays):
                                self.openOverlays[i][1].doKeyPress(event)

                        # Finally, trigger any registered event functions
                        self.fireEvent('onKeyPress', event)

                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        # Handle a mouse click on buttons
                        for button in self.openGUI[1].buttons:
                            if button.isHovered(pos):
                                button.onClick(self)

                        # Then, handle a mouse click on a text box
                        self.openGUI[1].currentTextBox = None
                        for t, textbox in enumerate(self.openGUI[1].textboxes):
                            if textbox.isHovered(pos):
                                self.openGUI[1].currentTextBox = t

                        # Finally, trigger any registered event functions
                        self.fireEvent('onMouseClick', event)

            # Get the time that the tick took to run
            deltaTime = time.time()-startTickTime
            # Sleep if running faster than 30 ticks per second
            if deltaTime < 1/util.FPS:
                time.sleep((1/util.FPS)-deltaTime)

    def drawClientGame(self, pos):
        '''
        Draw the game to the pygame display
        '''
        pygame.display.get_surface().fill((255, 255, 255))

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

    def getModInstance(self, modName):
        '''
        Return an instance of a mod with the given name
        '''
        return self.modLoader.mods.get(modName)

    def fireEvent(self, eventType, *args):
        '''
        Fire an event on the event bus
        '''
        for func in self.modLoader.gameRegistry.EVENT_BUS.get(eventType, []):
            func(self, *args)

    def fireCommand(self, text, username):
        '''
        Fire a command on either side
        '''
        # split the command and arguments
        command, *args = text.split()
        # Fetch the command class
        commandClass = self.modLoader.gameRegistry.commands.get(command)
        if commandClass is None:
            commandClass = self.modLoader.gameRegistry.commands.get('/failedCommand')
            args = [command]
        # Instantiate the command
        commandClass = commandClass(self)
        commandClass.run(username, *args)

    def openGui(self, guiID, *args):
        '''
        Open the GUI with the given id for this client
        '''
        if isinstance(self.openGUI, list):
            self.prevGUI = [self.openGUI[0], self.openGUI[1]]
        else:
            self.prevGUI = self.openGUI
        self.prevOverlays = list(self.openOverlays)

        self.openOverlays = []
        self.openGUI = [guiID, self.modLoader.gameRegistry.guis[guiID](*args)]

    def restoreGui(self):
        '''
        Restore the previous GUI state for the client
        '''
        if isinstance(self.prevGUI, list):
            self.openGUI = [self.prevGUI[0], self.prevGUI[1]]
        else:
            self.openGUI = self.prevGUI
        # self.openGUI = list(self.prevGUI)
        self.openOverlays = list(self.prevOverlays)
        self.prevGUI = None
        self.prevOverlays = []

    def openOverlay(self, guiID, *args):
        '''
        Add an overlay to be drawn to the screen
        '''
        self.openOverlays.append([guiID, self.modLoader.gameRegistry.guis[guiID](*args)])

    def isOverlayOpen(self, guiID):
        '''
        Return whether or not the given overlay is currently open
        '''
        for overlay in self.openOverlays:
            if overlay[0] == guiID:
                return True
        return False

    def closeGui(self):
        '''
        Close the currently open gui
        '''
        self.prevGUI = self.openGUI
        self.openGUI = None

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

    def getPlayerIndex(self, player):
        '''
        Get index of a given player object in the world player list
        '''
        try:
            if isinstance(player, str):
                index = [a.username == player for a in self.world.players].index(True)
            else:
                    playerList = self.modLoader.gameRegistry.dimensions[player.dimension].getWorldObj().players
                    index = [a.username == player.username for a in playerList].index(True)
        except ValueError:
            raise IndexError('Player is not in the list')
        return index

    def processCommandLineArgs(self, argHandler):
        '''
        Process the Command Line Arguments for the game
        '''
        import mods.default.server.server_mod as server
        import mods.default.neural_net as nn

        if argHandler.getRuntimeType() == util.SERVER:
            # Schedule the Server side mods to be loaded here
            self.modLoader.registerMod(server.ServerMod)

        elif argHandler.getRuntimeType() in [util.CLIENT, util.COMBINED]:
            import mods.default.client.client_mod as client

            if argHandler.getRuntimeType() == util.COMBINED:
                # Fork a new Server process, then set to connect to it immediately
                serverProcess = multiprocessing.Process(target=forkServer)
                serverProcess.daemon = True
                self.child = serverProcess
                serverProcess.start()

                argHandler.results['address'] = socket.getfqdn()

            # Schedule the Client side mods to be loaded here
            self.modLoader.registerMod(client.ClientMod)

        if argHandler.getRunSpecialAI():
            # Schedule the special Neural Network AI mod to be loaded
            self.modLoader.registerMod(nn.NNetAIMod)

        if argHandler.getShouldLoadCustomMods():
            # Schedule the loading of the extra custom mods
            # if they aren't disabled in the command line.
            for modName in open('modlist'):
                self.modLoader.registerModByName(modName)

        # Set the world generation seed
        self.modLoader.gameRegistry.seed = argHandler.getSeed()

        # Print a helpful message
        print('Starting Game in {} Mode'.format({util.SERVER : 'SERVER',
                                                 util.CLIENT : 'CLIENT',
                                                 util.COMBINED : 'COMBINED'
                                                }[argHandler.getRuntimeType()]))

def forkServer():
    '''
    Fork a new process to run the server in the background
    '''
    # import mod
    serverRuntime = Game(util.ArgumentHandler(['--type', 'SERVER']))
    serverRuntime.run()
