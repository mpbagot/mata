# Impor the Python Standard Libraries
from threading import Thread
import random
import time

# Import the mod files
from api.packets import *
from api.biome_c import *

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
    def __init__(self, dimensionHandler, generate=True):
        self.entities = []
        self.vehicles = []
        self.players = []

        self.dimHandler = dimensionHandler

        self.world = None

        if generate:
            t = Thread(target=self.generate)
            t.daemon = True
            t.start()

            self.isGenerating = True

    def generate(self):
        '''
        Generate the tile map of the world based on the dimensionHandler
        '''
        start = time.time()
        biomes = self.dimHandler.biomes
        biomeSize = self.dimHandler.biomeSize

        # Generate a small starting biome map
        width, height = (50, 50)
        biomeMap = BiomeMap(width, height)

        # Scatter some biomes in
        for y, row in enumerate(biomeMap.map):
            for x, tile in enumerate(row):
                biomeMap.map[y][x] = random.choice(biomes)

        # Zoom the biomes to a bigger size
        for i in range(biomeSize):
            biomeMap.zoom()

        print('\n'.join(['.'.join([a.__name__[0] for a in row[:50]]) for row in biomeMap.map[:50]]))

        # Choose tile types and generate entities, houses, trees, etc in the biomes
        biomeMap.finalPass()
        self.world = biomeMap

        print('Time taken:', time.time()-start,'seconds')

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
                    func(game, entityBackup, entityBackup.tickDamage)
            elif self.entities[e].tickDamage:
                # Trigger on Entity Damaged events
                for func in gameRegistry.eventFunctions.get('onEntityDamage'):
                    func(game, self.entities[e], self.entities[e].tickDamage)

        # Loop through the vehicles and update them
        for v in range(len(self.vehicles)):
            self.vehicles[v].onVehicleUpdate(game)
            # If they get destroyed, delete them, and trigger events
            if self.vehicles[v].isDestroyed:
                vehicleBackup = self.vehicles[v]
                del self.vehicles[v]
                # Trigger on Vehicle Destruction events
                for func in gameRegistry.eventFunctions.get('onVehicleDestroyed'):
                    func(game, vehicleBackup)

        # Loop through the players and disconnect them if they died
        for p in range(len(self.players)):
            if self.players[p].isDead:
                # If the player has died, disconnect them (because of permadeath)
                game.modLoader.mods['ServerMod'].packetPipeline.sendToPlayer(
                                                    DisconnectPacket('You have died'),
                                                    self.players[p].username)
            elif self.players[p].tickDamage:
                # Trigger on Player Damaged events
                for func in gameRegistry.eventFunctions.get('onPlayerDamage'):
                    func(game, self.players[p], self.players[p].tickDamage)


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

    def toBytes(self, pos):
        '''
        Return the world tilemap object as a bytestring representation
        '''
        return self.world.toBytes(pos)

    @staticmethod
    def fromBytes(byteString):
        '''
        Get a world object from a byteString
        '''
        world = WorldMP(None, False)
        # Get the biomemap from the string
        world.world = BiomeMap.fromBytes(byteString)
        return world

    def addPlayer(self, player):
        '''
        Add a player to the world
        '''
        while self.isGenerating:
            pass
        self.players.append(player)
