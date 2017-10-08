'''
biome.py
contains the api for biomes
biome objects contain tile type data, spawnable entity, item and vehicle lists
'''
import random
import math

class Biome:
    def __init__(self):
        self.tileTypes = []
        self.entityTypes = []
        self.itemTypes = []
        self.vehicleTypes = []
        self.plantTypes = []

        self.tileType = None
        self.plantType = None

class BiomeMap:
    def __init__(self, width, height):
        self.map = [[0 for column in range(width)] for row in range(height)]

    def zoom(self):
        '''
        Zoom the biomes to about 10x their current size
        '''
        # Expand out the map, filling extra spots with 0
        tileMap = []
        for r, row in enumerate(self.map):
            tileMap.append([])
            for a in row:
                tileMap[-1] += [a, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        print('zooming')

        cdef int y, x, dy, dx = 0
        # Loop until the map has been completely filled
        while not all([all(i) for i in tileMap]):
            for y, row in enumerate(tileMap):
                for x, tile in enumerate(row):
                    # If the tile is a biome
                    if tile and not isinstance(tile, list):
                        # Loop a 5x5 square around the tile
                        for dy in range(y-2, y+3):
                            for dx in range(x-2, x+3):
                                # If the tile we're looking at is not right near
                                # the initial tile, skip it
                                if abs(y-dy)+abs(x-dx) > 2:
                                    continue

                                # If any of the dx or dy values overflow the list indexes
                                # Loop back around to the other side of the map
                                if dy >= len(tileMap):
                                    dy -= len(tileMap)
                                if dx >= len(row):
                                    dx -= len(row)

                                # Replace the blank tile with a list of
                                # possible biome types for that tile.
                                if tileMap[dy][dx] == 0:
                                    tileMap[dy][dx] = [tile]
                                elif isinstance(tileMap[dy][dx], list):
                                    tileMap[dy][dx].append(tile)

            # Finally, loop through each tile, and pick a possible biome type for it
            for y in range(len(tileMap)):
                for x in range(len(tileMap[y])):
                    if isinstance(tileMap[y][x], list):
                        tileMap[y][x] = random.choice(tileMap[y][x])

        self.map = tileMap

    def finalPass(self):
        '''
        Generate the tile type of each square,
        and generate extra details like trees
        '''
        pass

    def toBytes(self, pos):
        '''
        Return a bytestring represenation of this BiomeMap
        '''
        return b''

    @staticmethod
    def fromBytes(data):
        '''
        Return a biomemap based on the given byte data
        '''
        return BiomeMap(5, 5)
