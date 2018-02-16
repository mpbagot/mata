# Impor the Python Standard Libraries
from threading import Thread
import random
import time
import noise
from copy import deepcopy

# Import the mod files
from api.packets import *
from api.biome import *
from api.entity import *

class DimensionHandler:
    def __init__(self, chunkProvider, world):
        self.chunkProvider = chunkProvider
        self.worldObj = world

    def getName(self):
        '''
        Return a name for the dimension
        '''
        return ''

    def getWorldObj(self):
        '''
        Return a World Object for the dimension
        '''
        return self.worldObj

    def getBiomeSize(self):
      '''
      Get the biome generation size for this DimensionHandler
      '''
      return self.chunkProvider.biomeSize

    def generate(self, pos, gameRegistry):
        '''
        Generate the world according to the ChunkProvider
        '''
        tileMap = self.chunkProvider.generate(pos, gameRegistry)
        self.worldObj.setTileMap(tileMap)

class ChunkProvider:
    def __init__(self, biomes, biomeSize):
        self.biomes = biomes
        self.biomeSize = biomeSize

    def generate(self, pos, gameRegistry):
        '''
        Generate the tile map of the world based on position and preset biomes
        '''
        raise NotImplementedError('ChunkProvider has no generate method.')

class WorldMP:
    def __init__(self):
        self.entities = []
        self.vehicles = []
        self.players = []

        self._world = None

    def setTileMap(self, tileMap):
        '''
        Set the tile map of the world
        '''
        self._world = tileMap

    def getTileMap(self):
        '''
        Return the world tilemap
        '''
        return self._world

    def isWorldLoaded(self):
        '''
        Return whether the world has been generated
        '''
        return bool(self._world)

    def spawnEntityInWorld(self, entity):
        '''
        Spawn a new entity instance into the world
        Return whether successful or not
        '''
        if not isinstance(entity, EntityBase) or not isinstance(entity.uuid, str):
            print('[WARNING] Invalid entity. Did you forget to set the UUID?')
            return False
        elif not entity.uuid.isnumeric():
            print('[WARNING] Invalid entity UUID. You forgot to run getUUIDForEntity in ModLoader')
            return False
        self.entities.append(entity)
        return True

    def tickUpdate(self, game):
        '''
        Run one tick of updates on the world and everything in it (SERVER-SIDE UPDATE)
        '''
        # Separate the Game Registry
        gameRegistry = game.modLoader.gameRegistry
        # Loop through the entities and update them
        for e in range(len(self.entities)):
            self.entities[e].aiHandler.runAITick()
            game.fireEvent('onEntityUpdate', self.entities[e])
            # If they die, delete them, and trigger events
            if self.entities[e].isDead:
                entityBackup = self.entities[e]
                del self.entities[e]
                # Trigger on Entity Death events
                game.fireEvent('onEntityDeath', entityBackup, entityBackup.tickDamage)
            elif self.entities[e].tickDamage:
                # Trigger on Entity Damaged events
                game.fireEvent('onEntityDamage', self.entities[e], self.entities[e].tickDamage)

        # Loop through the vehicles and update them
        for v in range(len(self.vehicles)):
            self.vehicles[v].onVehicleUpdate(game)
            game.fireEvent('onVehicleUpdate', self.vehicles[v])
            # If they get destroyed, delete them, and trigger events
            if self.vehicles[v].isDestroyed:
                vehicleBackup = self.vehicles[v]
                del self.vehicles[v]
                # Trigger on Vehicle Destruction events
                game.fireEvent('onVehicleDestroyed', vehicleBackup)

        # Loop through the players and update them
        for p in range(len(self.players)):
            if self.players[p].isDead:
                # If the player has died, fire an onDeath event
                game.fireEvent('onPlayerDeath', self.players[p])
            elif self.players[p].tickDamage:
                # Trigger on Player Damaged events
                game.fireEvent('onPlayerDamage', self.players[p], self.players[p].tickDamage)

    def getUpdateData(self, player):
        '''
        Collate the update data into a bytes object
        '''
        # TODO clip the data based on the user
        return (str([p.toBytes() for p in self.players])+'$$$'+str([e.toBytes() for e in self.entities])).replace('"', "'''").encode()

    def handleUpdate(self, updateBytes, game):
        '''
        Use the binary data to update the world
        '''
        # TODO Add entities and vehicles to this.
        players, entities = updateBytes.decode().split('$$$')

        # Loop the transferred players
        players = eval(players)
        players = [Player.fromBytes(p) for p in players]

        for player in players:
            game.fireEvent("onPlayerUpdate", player, self.players)

        # Loop the transferred entities
        entities = eval(entities)
        entities = [Entity.fromBytes(e, game.modLoader.gameRegistry.entities) for e in entities]

        for entity in entities:
            game.fireEvent('onEntitySync', entity, self.entities)

    def addPlayer(self, player):
        '''
        Add a player to the world
        '''
        for p in self.players:
            if p.username == player.username:
                return p
        player.pos = [0, 0]
        self.players.append(player)
        return player
