class Game:
    def __init__(self, modLoader, argHandler):
        self.modLoader = modLoader
        self.processCommandLineArgs(argHandler)

        # Load all of the registered mods
        self.modLoader.loadRegisteredMods()

    def run(self):
        '''
        Run the game after initialising all of the mods
        '''
        pass

    def processCommandLineArgs(self, argHandler):
        '''
        Process the Command Line Arguments for the game
        '''
        if argHandler.getRuntimeType() == util.SERVER:
            # Schedule the Server side mods to be loaded here
            pass
        elif argHandler.getRuntimeType() in [util.CLIENT, util.COMBINED]:
            if argHandler.getRuntimeType() == util.COMBINED:
                # Fork a new Server process, then set to connect to it immediately
                pass
            # Schedule the Client side mods to be loaded here
            pass

        if argHandler.getRunSpecialAI():
            # TODO Schedule the special Neural Network AI mod to be loaded
            # self.modLoader.registerMod(mod.NNetAIMod)
            pass

        if argHandler.getShouldLoadCustomMods():
            # Schedule the loading of the extra custom mods if they aren't disabled in the command line.
            for modName in open('modlist'):
                self.modLoader.registerModByName(modName)
