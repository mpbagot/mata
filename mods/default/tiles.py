from api.biome import Tile, Plant

# Tiles
class Grass(Tile):
    def __init__(self):
        self.setTileName('grass')

class Dirt(Tile):
    def __init__(self):
        self.setTileName('dirt')

class Water(Tile):
    def __init__(self):
        self.setTileName('water')

class Sand(Tile):
    def __init__(self):
        self.setTileName('sand')

class Gravel(Tile):
    def __init__(self):
        self.setTileName('gravel')

class Road(Tile):
    def __init__(self):
        self.setTileName('road')

# Plants
class GrassPlant(Plant):
    def __init__(self):
        self.setTileName('horse')

class TreePlant(Plant):
    def __init__(self):
        self.setTileName('bear')
