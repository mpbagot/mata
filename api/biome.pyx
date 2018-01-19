'''
biome.py
contains the api for biomes
biome objects contain tile type data, spawnable entity, item and vehicle lists
'''
import random
import math
#import pygame

#pygame.init()

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

        self.setTiles()

class TileMap:
    def __init__(self, width, height):
        self.map = [[0 for column in range(width)] for row in range(height)]

    def finalPass(self, tileNoise, detailNoise, resources):
        '''
        Generate the tile type of each square,
        and generate extra details like trees
        '''
        # Loop the tiles in the world map
        for r in range(len(self.map)):
            for t, tile in enumerate(self.map[r]):
                # Instantiate the tile
                tile = tile()
                # Set a tile type
                if tile.tileTypes:
                    i = int(tileNoise[r][t]*len(tile.tileTypes))
                    tile.tileIndex = i
                    try:
                        tile.tileTypes[i] = tile.tileTypes[i](resources)
                    except TypeError:
                        print(tile.tileTypes[i])

                # Set a plant
                if random.random() > 0.8 and tile.plantTypes:
                    i = random.randint(0, len(tile.plantTypes)-1)
                    tile.plantIndex = i
                    tile.plantTypes[i] = tile.plantTypes[i]()
                # Place the tile into the tilemap
                self.map[r][t] = tile
