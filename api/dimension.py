class DimensionHandler:
    def __init__(self, biomes, biomeSize):
        self.biomes = biomes
        self.biomeSize = biomeSize
        self.worldObj = WorldMP(self)

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
    def __init__(self, dimensionHandler):
        self.entities = []
        self.vehicles = []
        self.players = []

        width, height = (10000, 10000)
        self.world = [[0 for column in range(width)] for row in range(height)]
        print('finished')

        # TODO generate the tile map of the world based on the dimensionhandler

    def tickUpdate(self, gameRegistry):
        '''
        Run one tick of updates on the world and everything in it
        '''
        pass

    def getUpdateData(self):
        '''
        Collate the update data into a bytes object
        '''
        return b''

    def handleUpdate(self, updateBytes):
        '''
        Use the binary blob data to update the world
        '''
        pass

    def addPlayer(self, player):
        '''
        Add a player to the world
        '''
        self.players.append(player)
