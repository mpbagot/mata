from api.biome import Tile

class Grass(Tile):
    def __init__(self):
        self.setTileName('grass')
        super().__init__()

class Dirt(Tile):
    def __init__(self):
        self.setTileName('dirt')
        super().__init__()

class Water(Tile):
    def __init__(self):
        self.setTileName('water')
        super().__init__()

class Sand(Tile):
    def __init__(self):
        self.setTileName('sand')
        super().__init__()

class Gravel(Tile):
    def __init__(self):
        self.setTileName('gravel')
        super().__init__()

class Road(Tile):
    def __init__(self):
        self.setTileName('road')
        super().__init__()
