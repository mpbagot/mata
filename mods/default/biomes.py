from api.biome import Biome
from mods.default.tiles import *

class Forest(Biome):
    def setTiles(self):
        self.tileTypes = [Gravel, Dirt, Grass]

class Desert(Biome):
    def setTiles(self):
        self.tileTypes = [Sand]

class City(Biome):
    def setTiles(self):
        self.tileTypes = [Gravel, Grass]

class Ocean(Biome):
    def setTiles(self):
        self.tileTypes = [Water]
