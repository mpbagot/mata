# Impor the Python Standard Libraries
from threading import Thread
import random
import time
import noise

# Import the mod files
from api.packets import *
from api.biome import *

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

    def generate(self, pos):
        '''
        Generate the tile map of the world based on the dimensionHandler and position
        '''
        start = time.time()
        xPos, yPos = pos
        xPos = round(xPos)
        yPos = round(yPos)

        # Generate Simplex Noise for the world
        noiseMap = [[noise.snoise2(x, y, 8, 1.4, 0.45)/2+0.5 for x in range(xPos-150, xPos+151)] for y in range(yPos-105, yPos+106)]
        biomeSize = self.dimHandler.biomeSize
        biomeNoise = [[noise.snoise2(x, y, 7, 3, 0.6-(biomeSize*0.1))/2+0.5 for x in range(xPos-150, xPos+151)] for y in range(yPos-105, yPos+106)]
        detailNoise = []

        biomes = self.dimHandler.biomes

        # Generate an empty starting biome map
        width, height = (150, 90)
        biomeMap = TileMap(width, height)

        # Scatter some biomes in
        for y, row in enumerate(biomeMap.map):
            for x, tile in enumerate(row):
                biomeMap.map[y][x] = biomes[round(biomeNoise[y][x]*(len(biomes)-1))]

        # Choose tile types and generate entities, houses, trees, etc in the biomes
        biomeMap.finalPass(noiseMap, detailNoise)
        self.world = biomeMap

        print('Time taken: '+str(time.time()-start)+' seconds')

        return self

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
                for func in gameRegistry.EVENT_BUS.get('onEntityDeath', []):
                    func(game, entityBackup, entityBackup.tickDamage)
            elif self.entities[e].tickDamage:
                # Trigger on Entity Damaged events
                for func in gameRegistry.EVENT_BUS.get('onEntityDamage', []):
                    func(game, self.entities[e], self.entities[e].tickDamage)

        # Loop through the vehicles and update them
        for v in range(len(self.vehicles)):
            self.vehicles[v].onVehicleUpdate(game)
            # If they get destroyed, delete them, and trigger events
            if self.vehicles[v].isDestroyed:
                vehicleBackup = self.vehicles[v]
                del self.vehicles[v]
                # Trigger on Vehicle Destruction events
                for func in gameRegistry.EVENT_BUS.get('onVehicleDestroyed', []):
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
                for func in gameRegistry.EVENT_BUS.get('onPlayerDamage', []):
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
        return self.world.toBytes(self.dimHandler.biomes)

    @staticmethod
    def fromBytes(byteString):
        '''
        Get a world object from a byteString
        '''
        world = WorldMP(None, False)
        # Get the biomemap from the string
        world.world = TileMap.fromBytes(byteString, self.dimHandler.biomes)
        return world

    def addPlayer(self, player):
        '''
        Add a player to the world
        '''
        player.pos = [0, 0]
        self.players.append(player)
        return player
