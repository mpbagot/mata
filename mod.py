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
        self.commands = []
        self.packetPipelines = {}
        self.audioEffects = {}
        self.eventFunctions = {}
        self.properties = {}

    def registerItem(self, itemClass):
        '''
        Register an item
        '''
        if self.items.get(itemClass.getRegistryName()) == None:
            self.items[itemClass.getRegistryName()] = itemClass
            return
        raise KeyError('Registry name {} already in use by another item!'.format(itemClass.getRegistryName()))

    def registerBiome(self, biomeClass):
        '''
        Register a biome, for the default dimension
        To register a biome with another dimension, use the DimensionHandler class
        '''
        if self.biomes.get(biomeClass.getRegistryName()) == None:
            self.biomes[biomeClass.getRegistryName()] = biomeClass
            return
        raise KeyError('Registry name {} already in use by another biome!'.format(biomeClass.getRegistryName()))

    def registerEntity(self, entityClass):
        '''
        Register an entity
        '''
        if self.entities.get(entityClass.getRegistryName()) == None:
            self.entities[entityClass.getRegistryName()] = entityClass
            return
        raise KeyError('Registry name {} already in use by another entity!'.format(entityClass.getRegistryName()))

    def registerGUI(self, guiClass):
        '''
        Register a GUI screen
        '''
        self.guis[len(self.guis)] = guiClass
        return len(self.guis)-1

    def registerVehicle(self, vehicleClass):
        '''
        Register a rideable vehicle
        '''
        if self.vehicles.get(vehicleClass.getRegistryName()) == None:
            self.vehicles[vehicleClass.getRegistryName()] = vehicleClass
            return
        raise KeyError('Registry name {} already in use by another vehicle!'.format(vehicleClass.getRegistryName()))

    def registerCommand(self, commandClass):
        '''
        Register a console command (for admins and moderators)
        '''
        self.commands.append(commandClass)

    def registerDimension(self, dimensionClass):
        '''
        Register a dimension
        '''
        self.dimensions[len(self.dimensions)] = dimensionClass
        return len(self.dimensions)-1

    def registerEventHandler(self, eventFunction, eventType):
        '''
        Register an event handling function
        '''
        self.eventFunctions[eventType] = self.eventFunctions.get(eventType, [])+[eventFunction]

    def registerAudioEffect(self, audioClass):
        '''
        Register an audio effect
        '''
        if self.audioEffects.get(audioClass.getRegistryName()) == None:
            self.audioEffects[audioClass.getRegistryName()] = audioClass
            return
        raise KeyError('Registry name {} already in use by another audio effect!'.format(audioClass.getRegistryName()))


    def registerPacketHandler(self, packetHandler):
        '''
        Register a packet handler and any assosciated packets
        '''
        self.packetPipelines[len(self.packetPipelines)] = packetHandler
        return len(self.packetPipelines)-1

    def registerProperties(self, propertyClass):
        '''
        Register object properties
        '''
        self.properties[propertyClass.objectType] = self.properties.get(propertyClass.objectType, [])+[propertyClass]

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
                        'DimensionHandler' : self.registerDimension,
                        'Properties' : self.registerProperties
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
