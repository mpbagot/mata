'''
mod.py
Module containing the Mod loading and Mod API code for the game
'''
# Import the Python3 standard libraries
import os

from api.cmd import FailedCommand, MessageCommand

class ModLoader:
    def __init__(self, game):
        self.modsToLoad = []
        self.mods = {}
        self.game = game
        self.gameRegistry = GameRegistry()

    def getUUIDForEntity(self, entity):
        '''
        Generate and assign a unique id for a new entity to place in the world
        '''
        # Get the current number of entities and vehicles in all the dimensions
        entity_length = 0
        for dimension in self.gameRegistry.dimensions:
            world = self.game.getWorld(dimension)
            entity_length += len(world.entities)+len(world.vehicles)

        # Hash and set the uuid
        entity.uuid = str(hash(entity.name+str(entity_length)))

    def registerModByName(self, name):
        '''
        Search the mod folder for a mod with the given mod name, and load it
        '''
        # Traverse the python files in the mod folder
        for filename in os.listdir('mods'):
            if filename.endswith('.py'):
                exec('import mods.'+filename[:-3]+' as module')
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
        if not issubclass(modClass, Mod):
            raise Exception('Illegal Class type of \'{}\'. Expected child of \'Mod\''.format(modClass.__name__))
        self.modsToLoad.append(modClass)

    def loadRegisteredMods(self):
        '''
        Load all of the registered mods
        '''
        # Instantiate the mods
        self.mods = {mod.modName : mod(self.gameRegistry, self.game) for mod in self.modsToLoad}

        # Run the Preload, Load, and PostLoad on each instance
        for modName in self.mods:
            modInstance = self.mods[modName]
            modInstance.preLoad()
        for modName in self.mods:
            modInstance = self.mods[modName]
            modInstance.load()
        for modName in self.mods:
            modInstance = self.mods[modName]
            modInstance.postLoad()

class GameRegistry:
    def __init__(self):
        self.entities = {}
        self.items = {}
        self.guis = {}
        self.dimensions = {}
        self.vehicles = {}
        self.commands = {
                         '/failedCommand' : FailedCommand,
                         '/message' : MessageCommand
                        }
        self.packetPipelines = {}
        self.audioEffects = {}
        self.resources = {}
        self.EVENT_BUS = {}
        self.properties = {}
        self.seed = 0

    def registerItem(self, itemClass):
        '''
        Register an item
        '''
        if self.items.get(itemClass.getRegistryName()) is None:
            self.items[itemClass.getRegistryName()] = itemClass
            return
        raise KeyError('[ERROR] Registry name {} already in use by another item!'.format(itemClass.getRegistryName()))

    def registerEntity(self, entityClass):
        '''
        Register an entity
        '''
        if self.entities.get(entityClass.getRegistryName()) is None:
            self.entities[entityClass.getRegistryName()] = entityClass.__class__
            return
        raise KeyError('[ERROR] Registry name {} already in use by another entity!'.format(entityClass.getRegistryName()))

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
        if self.vehicles.get(vehicleClass.getRegistryName()) is None:
            self.vehicles[vehicleClass.getRegistryName()] = vehicleClass.__class__
            return
        raise KeyError('[ERROR] Registry name {} already in use by another vehicle!'.format(vehicleClass.getRegistryName()))

    def registerCommand(self, commandText, commandClass):
        '''
        Register a console command (for admins and moderators)
        '''
        self.commands[commandText] = commandClass

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
        self.EVENT_BUS[eventType] = self.EVENT_BUS.get(eventType, [])+[eventFunction]

    def registerResource(self, resourceId, resource):
        '''
        Register a non-audio resource
        '''
        self.resources[resourceId] = resource

    def registerAudioEffect(self, audioClass):
        '''
        Register an audio effect
        '''
        if self.audioEffects.get(audioClass.getRegistryName()) is None:
            self.audioEffects[audioClass.getRegistryName()] = audioClass
            return
        raise KeyError('[ERROR] Registry name {} already in use by another audio effect!'.format(audioClass.getRegistryName()))


    def registerPacketHandler(self, packetHandler):
        '''
        Register a packet handler and any assosciated packets
        '''
        self.packetPipelines[len(self.packetPipelines)] = packetHandler
        return len(self.packetPipelines)-1

    def registerProperties(self, propertyObj, objectType):
        '''
        Register object properties
        '''
        self.properties[objectType] = self.properties.get(objectType, [])+[propertyObj]

class Mod:
    modName = 'Mod'

    def __init__(self, gameRegistry, game):
        self.gameRegistry = gameRegistry
        self.game = game

    def preLoad(self):
        '''
        Run the preload registers
        '''
        raise NotImplementedError('[ERROR] PreLoad function not overridden in mod '+self.__class__.modName)

    def load(self):
        '''
        Run the load registers
        '''
        raise NotImplementedError('[ERROR] Load function not overridden in mod '+self.__class__.modName)

    def postLoad(self):
        '''
        Run the postload registers
        '''
        raise NotImplementedError('[ERROR] PostLoad function not overridden in mod '+self.__class__.modName)
