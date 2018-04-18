'''
Util module
This module contains miscellaneous classes and constants that are used by the game engine
'''
import pygame
import math

SERVER = 0
CLIENT = 1
COMBINED = 2

DEFAULT_PORT = 6658
MAX_PLAYERS = 100
FPS = 60

DISPLAY_FLAGS = pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.RESIZABLE

def calcChecksum(data):
    '''
    Calculate a checksum
    '''
    checksum = 0
    for a in range(len(data)):
        checksum += data[a]
    return checksum.to_bytes(3, 'big')

def calcDistance(ent1, ent2):
    '''
    Calculate the distance between two entities
    '''
    dimensionDelta = (ent1.dimension-ent2.dimension) * 1000
    deltaPos = [ent1.pos[a]-ent2.pos[a] for a in (0, 1)]
    return (deltaPos[0]**2 + deltaPos[1]**2)**0.5 + dimensionDelta

def calcDirection(pos1, pos2):
    '''
    Calculate a direction between two positions
    pos1 is current position
    pos2 is previous position
    '''
    theta = math.atan2(pos1[0]-pos2[0], pos1[1]-pos2[1])/math.pi
    return theta

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

            elif arg == "--seed" and i != len(self.args)-1:
                try:
                    x = float(self.args[i+1])
                except ValueError:
                    x = 0
                self.results['seed'] = (4*x)/(x**2+1)
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

    def getSeed(self):
        '''
        Return the world generation seed
        '''
        return self.results.get('seed', 0)

    def getConnectingAddress(self):
        '''
        Return the address that this client is going to connect to
        '''
        return self.results.get('address', '')
