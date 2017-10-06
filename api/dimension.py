# Impor the Python Standard Libraries
from threading import Thread

# Import the mod files
from api.packets import *

class DimensionHandler:
    def __init__(self, biomes, biomeSize):
        self.biomes = biomes
        self.biomeSize = biomeSize
        self.worldObj = WorldMP(self)

    def saveToFile(self):
        '''
        Write the dimension data to a file (Run on Server Side Only)
        '''
        pass

    def readFromFile(self):
        '''
        Read the dimension data from a file (Run on Server Side Only)
        '''
        pass

    def getWorldObj(self):
        '''
        Return a World Object for the dimension
        '''
        return self.worldObj

class WorldMP:
    def __init__(self, dimensionHandler):
        self.entities = []
        self.vehicles = []
        self.players = []

        self.dimHandler = dimensionHandler

        self.world = None

        t = Thread(target=self.generate)
        t.daemon = True
        t.start()

        self.isGenerating = True

    def generate(self):
        '''
        Generate the tile map of the world based on the dimensionHandler
        '''
        # TODO generate the tile map of the world based on the dimensionhandler
        width, height = (10000, 10000)
        self.world = [[0 for column in range(width)] for row in range(height)]
        self.isGenerating = False

    def tickUpdate(self, game):
        '''
        Run one tick of updates on the world and everything in it
        '''
        # Separate the Game Registry
        gameRegistry = game.modLoader.gameRegistry
        # Loop through the entities and update them
        for e in range(len(self.entities)):
            self.entities[e].onLivingUpdate(game)
            # If they die, delete them, and trigger events
            if self.entities[e].isDead:
                entityBackup = self.entities[e]
                del self.entities[e]
                # Trigger on Entity Death events
                for func in gameRegistry.eventFunctions.get('onEntityDeath'):
                    func(game, entityBackup)

        # Loop through the vehicles and update them
        for v in range(len(self.vehicles)):
            self.vehicles[v].onVehicleUpdate(game)
            # If they get destroyed, delete them, and trigger events
            if self.vehicles[v].isDestroyed:
                vehicleBackup = self.vehicles[v]
                del self.vehicles[v]
                # Trigger on Entity Death events
                for func in gameRegistry.eventFunctions.get('onVehicleDestroyed'):
                    func(game, entityBackup)

        # Loop through the players and disconnect them if they died
        for p in range(len(self.players)):
            if self.players[p].isDead:
                # If the player has died, disconnect them (because of permadeath)
                game.modLoader.mods['ServerMod'].packetPipeline.sendToPlayer(
                                                    DisconnectPacket('You have died'),
                                                    self.players[p].username)

    def getUpdateData(self):
        '''
        Collate the update data into a bytes object
        '''
        return b''

    def handleUpdate(self, updateBytes):
        '''
        Use the binary blob data to update the world
        '''
        pass

    def toBytes(self):
        '''
        Return the entire world object as a bytestring representation
        '''
        return b'this is world data fsdlfaslkdf'

    @staticmethod
    def fromBytes(byteString):
        '''
        Get a world object from a byteString
        '''
        return WorldMP(None)

    def addPlayer(self, player):
        '''
        Add a player to the world
        '''
        while self.isGenerating:
            pass
        self.players.append(player)
