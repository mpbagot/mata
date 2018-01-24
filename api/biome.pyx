'''
biome.py
contains the api for biomes
biome objects contain tile type data, spawnable entity, item and vehicle lists
'''
import random
import math

class Tile:
    def __init__(self, resources):
        try:
            self.img = resources['tile_'+self.getTileName()]
        except Exception:
            raise Exception('Selected Resource has not been registered!')
        # self.img = pygame.image.load(self.getResourceLocation())

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
          self.tileTypes[self.tileIndex] = self.tileTypes[self.tileIndex].__class__(resources)

    def setTileType(self, tileNoise, detailNoise, resources):
        '''
        Setup the tile type and plant type for this tile
        '''
        # Initialise the tile and set the type
        if self.tileTypes:
            i = int(tileNoise*len(self.tileTypes))
            self.tileIndex = i
            try:
                self.tileTypes[i] = self.tileTypes[i](resources)
            except TypeError:
                print(self.tileTypes[i])

        # Set a plant
        if random.random() > 0.8 and self.plantTypes:
            i = random.randint(0, len(self.plantTypes)-1)
            self.plantIndex = i
            self.plantTypes[i] = self.plantTypes[i]()


class TileMap:
    def __init__(self, width, height):
        self.map = [[0 for column in range(width)] for row in range(height)]
