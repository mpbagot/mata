'''
Util module
This module contains miscellaneous classes and constants that are used by the game engine
'''
SERVER = 0
CLIENT = 1
COMBINED = 2

DEFAULT_PORT = 6543
MAX_PLAYERS = 100

class ArgumentHandler:
    '''
    An object to store and handle the command line arguments passed into the game at runtime
    '''
    def __init__(self, arguments):
        self.results = {}
        self.args = arguments
        self.handleArgs()

    def handleArgs(self):
        '''
        Process the arguments passed in, and set the results dictionary accordingly
        '''
        # Iterate the arguments and handle them
        i = 0
        while i < len(self.args):
            arg = self.args[i]
            # Handle the mod toggle argument
            if arg == '--disableMods':
                self.results['loadCustomMods'] = False

            # Handle the runtime type argument, defaulting to server if invalid
            elif arg == '--type' and i != len(self.args)-1:
                self.results['runtimeType'] = {'SERVER' : SERVER,
                                               'CLIENT' : CLIENT,
                                               'COMBINED' : COMBINED
                                              }.get(self.args[i+1], SERVER)
                del self.args[i+1]

            # Handle the address and port arguments
            elif arg == '--address' and i != len(self.args)-1:
                self.results['address'] = self.args[i+1]
                del self.args[i+1]
            elif arg == '--port' and i != len(self.args)-1:
                self.results['port'] = self.args[i+1]
                del self.args[i+1]

            # Handle the AI argument
            elif arg == '--enableSpecialAI':
                self.results['specialAI'] = True

            # Print a warning message if an unknown argument is given
            else:
                print('[WARNING] Unknown argument: {}'.format(arg))
            del self.args[i]

    def getRuntimeType(self):
        '''
        Return the type of game being run, either client, server, or combined
        '''
        return self.results.get('runtimeType', COMBINED)

    def getRunSpecialAI(self):
        '''
        Return whether or not to run the neural network ai, as opposed to the normal ai
        '''
        return self.results.get('specialAI', False)

    def getShouldLoadCustomMods(self):
        '''
        Return whether to load custom mods, beyond the default game
        '''
        return self.results.get('loadCustomMods', True)

    def getConnectingAddress(self):
        '''
        Return the address and port that this client is going to connect to
        '''
        try:
            return (self.results['address'], self.results['port'])
        except KeyError:
            return None
