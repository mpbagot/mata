# Import the game's modules
import util
import mods.default.client.client_mod as client
import mods.default.server.server_mod as server
import mods.default.neural_net as nn

# Import the standard libraries
import time
import multiprocessing
import os

class Game:
    def __init__(self, modLoader, argHandler):
        self.modLoader = modLoader
        self.processCommandLineArgs(argHandler)

        # Load all of the registered mods
        self.modLoader.loadRegisteredMods()
        # Set the world up
        self.world = self.modLoader.gameRegistry.getWorld()

    def run(self):
        '''
        Run the game after initialising all of the mods
        '''
        # Run at 30 ticks per second
        while True:
            # Get the start time of the tick
            startTickTime = time.time()
            # TODO run the tick here
            for func in self.modLoader.gameRegistry.eventFunctions.get('onTick', []):
                func(self)

            deltaTime = time.time()-startTickTime
            # Sleep if running faster than 30 ticks per second
            if deltaTime < 1/30:
                time.sleep((1/30)-deltaTime)

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
                t = multiprocessing.Process(target=forkServer)
                t.daemon = True
                t.start()
            # Schedule the Client side mods to be loaded here
            self.modLoader.registerMod(client.ClientMod)

        if argHandler.getRunSpecialAI():
            # Schedule the special Neural Network AI mod to be loaded
            self.modLoader.registerMod(nn.NNetAIMod)

        if argHandler.getShouldLoadCustomMods():
            # Schedule the loading of the extra custom mods if they aren't disabled in the command line.
            for modName in open('modlist'):
                self.modLoader.registerModByName(modName)

        # Print a helpful message
        print('Starting Game in {} Mode'.format({util.SERVER : 'SERVER', util.CLIENT : 'CLIENT',
                                                util.COMBINED : 'COMBINED'}[argHandler.getRuntimeType()]))

def forkServer():
    import mod
    serverRuntime = Game(mod.ModLoader(), util.ArgumentHandler(['--type', 'SERVER']))
    serverRuntime.run()
