from api.biome import Tile

class Grass(Tile):
    def __init__(self, resources):
        self.setTileName('grass')
        super().__init__(resources)

class Dirt(Tile):
    def __init__(self, resources):
        self.setTileName('dirt')
        super().__init__(resources)

class Water(Tile):
    def __init__(self, resources):
        self.setTileName('water')
        super().__init__(resources)

class Sand(Tile):
    def __init__(self, resources):
        self.setTileName('sand')
        super().__init__(resources)

class Gravel(Tile):
    def __init__(self, resources):
        self.setTileName('gravel')
        super().__init__(resources)

class Road(Tile):
    def __init__(self, resources):
        self.setTileName('road')
        super().__init__(resources)
