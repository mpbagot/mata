'''
mod.py
Module containing the Mod loading and Mod API code for the game
'''
# Import the Python3 standard libraries
import os

class ModLoader:
    def __init__(self):
        self.modsToLoad = []
        self.gameRegistry = GameRegistry()

    def registerModByName(self, name):
        '''
        Search the mod folder for a mod with the given mod name, and load it
        '''
        # Traverse the python files in the mod folder
        for f in os.listdir('mods'):
            if f.endswith('.py'):
                exec('import mods.'+f[:-3]+' as module')
                # Check if the mod class is in the file
                if name in dir(module):
                    modClass = eval('module.'+name)
                    # Register it normally if it is
                    self.registerMod(modClass)
                    return
        # Error if the mod doesn't exist
        raise FileNotFoundError('Mod File not Found in \'mods\' folder')

    def registerMod(self, modClass):
        '''
        Load a mod from a class that is a child of 'Mod'
        '''
        # Error if the mod is not valid
        if not isinstance(modClass, Mod):
            raise Exception('Illegal Class type of \'{}\'. Expected child of \'Mod\''.format(modClass.__class__.__name__))
        self.modsToLoad.append(modClass)

    def loadRegisteredMods(self):
        '''
        Load all of the registered mods
        '''
        # Instantiate the mods
        mods = [mod(self.gameRegistry) for mod in self.modsToLoad]

        # Run the Preload, Load, and PostLoad on each instance
        for modInstance in mods:
            modInstance.preLoad()
        for modInstance in mods:
            modInstance.load()
        for modInstance in mods:
            modInstance.postLoad()

class GameRegistry:
    def __init__(self):
        self.entities = {}
        self.items = {}
        self.guis = {}
        self.dimensions = {}
        self.biomes = {}
        self.vehicles = {}
        self.commands = {}
        self.packetPipelines = {}
        self.audioEffects = {}
        self.eventFunctions = {}

    def registerItem(self, itemClass):
        '''
        Register an item
        '''
        pass

    def registerBiome(self, biomeClass):
        '''
        Register a biome, for the default dimension
        To register a biome with another dimension, use the DimensionHandler class
        '''
        pass

    def registerEntity(self, entityClass):
        '''
        Register an entity
        '''
        pass

    def registerGUI(self, guiClass):
        '''
        Register a GUI screen
        '''
        pass

    def registerVehicle(self, vehicleClass):
        '''
        Register a rideable vehicle
        '''
        pass

    def registerCommand(self, commandClass):
        '''
        Register a console command (for admins and moderators)
        '''
        pass

    def registerDimension(self, dimensionClass):
        '''
        Register a dimension
        '''
        pass

    def registerEventHandler(self, eventFunction, eventType):
        '''
        Register an event handling function
        '''
        pass

    def registerAudioEffect(self, audioClass):
        '''
        Register an audio effect
        '''
        pass

    def registerPacketHandler(self, packetHandler):
        '''
        Register a packet handler and any assosciated packets
        '''
        pass

    def register(self, registerObj):
        '''
        Register an object without regard for its type, except events
        '''
        registryTypes = {'AudioFX' : self.registerAudioEffect,
                        'Command' : self.registerCommand,
                        'PacketHandler' : self.registerPacketHandler,
                        'Entity' : self.registerEntity,
                        'Item' : self.registerItem,
                        'Biome' : self.registerBiome,
                        'Vehicle' : self.registerVehicle,
                        'GUI' : self.registerGUI,
                        'DimensionHandler' : self.registerDimension
                        }
        register = registryTypes.get(registerObj.__class__.__name__)
        if register is None:
            raise TypeError('Object being registered is of an invalid type \'{}\''.format(registerObj.__class__.__name__))
        register(registerObj)

class Mod:
    def __init__(self, gameRegistry):
        self.gameRegistry = gameRegistry
        self.initialiseProperties()

    def initialiseProperties(self):
        '''
        Initialise the properties of the mod. Currently:
        self.modName
        '''
        raise NotImplementedError('A mod hasn\'t initialised its properties correctly.')

    def preLoad(self):
        '''
        Run the preload registers
        '''
        raise NotImplementedError('PreLoad function not overridden in mod '+self.modName)

    def load(self):
        '''
        Run the load registers
        '''
        raise NotImplementedError('Load function not overridden in mod '+self.modName)

    def postLoad(self):
        '''
        Run the postload registers
        '''
        raise NotImplementedError('PostLoad function not overridden in mod '+self.modName)
