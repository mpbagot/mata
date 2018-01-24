from api.biome import Biome
from mods.default.tiles import *

class Forest(Biome):
    def initTiles(self):
        self.tileTypes = [Gravel, Dirt, Grass]

class Desert(Biome):
    def initTiles(self):
        self.tileTypes = [Sand]

class City(Biome):
    def initTiles(self):
        self.tileTypes = [Gravel, Grass]

class Ocean(Biome):
    def initTiles(self):
        self.tileTypes = [Water]
