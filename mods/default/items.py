'''
items.py
A module with definitions of all the default items for MATA
'''
from api.item import *

class Dirt(Item):
    def __init__(self, resources):
        super().__init__(resources)
        self.setRegistryName('dirt')
        self.image = 'tile_dirt'
