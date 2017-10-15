'''
biome.py
contains the api for biomes
biome objects contain tile type data, spawnable entity, item and vehicle lists
'''
import random
import math
import pygame

pygame.init()

class Tile:
    def __init__(self):
        self.img = pygame.image.load(self.getResourceLocation())

    def setTileName(self, name):
        '''
        Set the tile name
        '''
        self.name = name

    def getResourceLocation(self):
        '''
        Return the tile image location
        '''
        return 'resources/textures/mods/tiles/{}.png'.format(self.name)

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

    def toBytes(self, biomes):
        biomeId = biomes.index(self.__class__).to_bytes(1, 'big')
        return biomeId+(self.tileIndex+1).to_bytes(1, 'big')+(self.plantIndex+1).to_bytes(1, 'big')

    @staticmethod
    def fromBytes(data, biomes):
        biomeId, tileIndex, plantIndex = list(data)
        tile = biomes[biomeId]()
        tile.tileIndex = tileIndex - 1
        tile.plantIndex = plantIndex - 1
        tile.tileTypes[tile.tileIndex] = tile.tileTypes[tile.tileIndex]()
        return tile

class TileMap:
    def __init__(self, width, height):
        self.map = [[0 for column in range(width)] for row in range(height)]

    @staticmethod
    def createFromTiles(tiles):
        '''
        Create a TileMap from a tile array
        '''
        tileMap = TileMap(5, 5)
        print(len(tiles))
        tileMap.map = tiles
        return tileMap

    def finalPass(self, tileNoise, detailNoise):
        '''
        Generate the tile type of each square,
        and generate extra details like trees
        '''
        for r, row in enumerate(self.map):
            for t, tile in enumerate(row):
                tile = tile()
                self.map[r][t] = tile
                if len(tile.tileTypes):
                    self.map[r][t].tileIndex = round(tileNoise[r][t]*(len(tile.tileTypes)-1))
                else:
                    self.map[r][t].tileIndex = -1

                if random.random() > 0.8 and len(tile.plantTypes):
                    self.map[r][t].plantIndex = random.randint(0, len(tile.plantTypes)-1)
                else:
                    self.map[r][t].plantIndex = -1

    def toBytes(self, biomes):
        '''
        Return a bytestring representation of this TileMap
        '''
        # Generate the byte string and return it
        byteString = b''
        for row in self.map:
            for tile in row:
                # Append biome id, tile index, plant index
                byteString += tile.toBytes(biomes)
            byteString += '|'.encode()
        return byteString

    @staticmethod
    def fromBytes(data, biomes):
        '''
        Return a biomemap based on the given byte data
        '''
        world = TileMap(1, 1)
        # Split the data up into a 2D array
        # rows = [a for a in data.split('|'.encode()) if a]
        # tiles = [[row[a:a+3] for a in range(0, len(row), 3)] for row in rows]

        # Generate a tileMap from the bytes
        tileMap = []
        for row in [a for a in data.split('|'.encode()) if a]:
            tileMap.append([])
            for a in range(0, len(row), 3):
                tileMap[-1].append(Biome.fromBytes(row[a:a+3], biomes))

        world.map = tileMap
        return world
