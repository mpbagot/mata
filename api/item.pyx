'''
item.py
A module to hold all the api stuff related to items
'''

class Inventory:
    def __init__(self):
        self.items = {'left' : Item({}), 'right' : Item({}), 'hotbar' : [], 'main' : []}

    def getEquipped(self):
        return [self.items['left'], self.items['right']]

    @staticmethod
    def fromBytes(byte):
        return Inventory()

    def toBytes(self):
        return b''

class Item:
    def __init__(self, resources):
        try:
            self.img = resources['item_'+self.getItemName()]
        except KeyError:
            import pygame
            self.img = pygame.image.load('resources/textures/mods/tiles/dirt.png')
            #raise Exception('Item Image has not been Registered!')

    def getItemName(self):
        return 'null_item'

    def hasAttribute(self, name):
        '''
        Return whether the class (and classes which extend this) has a given attribute
        '''
        try:
            a = self.__getattribute__(name)
            return True
        except AttributeError:
            return False

class ItemStack:
    def __init__(self, item, size):
        self.stackSize = size
        self.item = item
