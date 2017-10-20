'''
item.py
A module to hold all the api stuff related to items
'''
#import pygame

class Inventory:
    def __init__(self):
        self.items = {'left' : Item(), 'right' : Item(), 'hotbar' : [], 'main' : []}

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
            raise Exception('Item Image has not been Registered!')
#        self.img = pygame.image.load('resources/textures/mods/tiles/dirt.png')

class ItemStack:
    pass
