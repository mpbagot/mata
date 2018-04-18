from api.vehicle import *

from random import randint

class Horse(Vehicle):
    def __init__(self):
        super().__init__()
        self.setRegistryName('Horse')
        self.setImage('vehicle_horse')
        self.pos = [randint(-5, 5), randint(-5, 5)]
        self.speed = 30

    def getMaxRiders(self):
        '''
        Return the number of players that can ride a horse at one time
        '''
        return 2
