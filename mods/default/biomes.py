from api.biome import Biome, NullPlant
from mods.default.tiles import *

class Forest(Biome):
    def initTiles(self):
        self.tileTypes = [Dirt, Grass, Gravel]
        self.plantTypes = [NullPlant, GrassPlant, TreePlant, TreePlant]

class Desert(Biome):
    def initTiles(self):
        self.tileTypes = [Sand]
        self.plantTypes = [NullPlant, GrassPlant]

class City(Biome):
    def initTiles(self):
        self.tileTypes = [Gravel, Grass]

class Ocean(Biome):
    def initTiles(self):
        self.tileTypes = [Water]
