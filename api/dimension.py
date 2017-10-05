class DimensionHandler:
    def __init__(self, biomes, biomeSize):
        self.biomes = biomes
        self.biomeSize = biomeSize
        self.worldObj = WorldMP(self, self.entities, self.items, self.vehicles)

    def saveToFile(self):
        '''
        Write the dimension data to a file (Run on Server Side Only)
        '''
        pass

    def readFromFile(self):
        '''
        Read the dimension data from a file (Run on Server Side Only)
        '''
        pass

    def getWorldObj(self):
        '''
        Return a World Object for the dimension
        '''
        return self.worldObj

class WorldMP:
    def __init__(self, dimensionHandler, entityList, itemList, vehicleList):
        self.entities = []
        self.vehicles = []
        self.players = []

        width, height = (10000, 10000)
        self.world = [[0 for column in width] for row in height]

        # TODO generate the tile map of the world based on the four parameters
