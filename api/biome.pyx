'''
biome.py
contains the api for biomes
biome objects contain tile type data, spawnable entity, item and vehicle lists
'''
import random
import math

class Tile:
    def getImage(self, resources):
        try:
            return resources['tile_'+self.getTileName()]
        except Exception:
            raise Exception('Selected Resource has not been registered!')

    def setTileName(self, name):
        '''
        Set the tile name
        '''
        self.name = name

    def getTileName(self):
        return self.name

    def getResourceLocation(self):
        '''
        Return the tile image location
        '''
        return 'resources/textures/mods/tiles/{}.png'.format(self.getTileName())

class Plant(Tile):
    pass

class NullPlant(Plant):
    def __init__(self):
        self.setTileName('null_obj')

class Biome:
    def __init__(self):
        self.tileTypes = []
        self.entityTypes = []
        self.itemTypes = []
        self.vehicleTypes = []
        self.plantTypes = []

        self.tileIndex = -1
        self.plantIndex = -1

        self.initTiles()

    def initTiles(self):
        '''
        Initialise the tile types
        '''
        raise NotImplementedError('This method should be overridden by a subclass')

    def resetTile(self, resources):
        '''
        Reset the Pygame surface for this tile
        '''
        if self.tileIndex >= 0:
            self.tileTypes[self.tileIndex] = self.tileTypes[self.tileIndex].__class__()
        if self.plantIndex >= 0:
            self.plantTypes[self.plantIndex] = self.plantTypes[self.plantIndex].__class__()

    def setTileType(self, tileNoise, detailNoise, resources):
        '''
        Setup the tile type and plant type for this tile
        '''
        # Initialise the tile and set the type
        if self.tileTypes:
            i = int(tileNoise * len(self.tileTypes))
            self.tileIndex = i
            self.tileTypes[i] = self.tileTypes[i]()

        # Set a plant
        # 0.5 is the minimum threshold for details
        if self.plantTypes:
            # Calculate the plant/detail index
            i = int((2 * detailNoise - 1) * len(self.plantTypes))
            # i = max(0, (20 * detailNoise - 11)//3)
            self.plantIndex = i
            # Then instantiate the detail object
            self.plantTypes[i] = self.plantTypes[i]()

class TileMap:
    def __init__(self, width, height):
        self.map = [[0 for column in range(width)] for row in range(height)]
