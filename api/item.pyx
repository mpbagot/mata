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

    def hashInv(self):
        return ''

    def sortItems(self):
        self.sortGroup('hotbar')
        self.sortGroup('main')

    def sortGroup(self, name):
        used = []
        for i, itemstack in self.items[name]:
            if i in used:
                continue
            for j, item in self.items[name]:
                if j != i and item.getItemName() == itemstack.getItemName():
                    used.append(j)
                    result, carryover = itemstack.add(item)
                    self.items[name][i] = result
                    self.items[name][j] = carryover

    @staticmethod
    def addInventory(inv1, inv2):
        '''
        Return an inventory that is the sum of two inventories
        '''
        sumInv = Inventory()
        sumInv.items = inv1.items

        sumInv.items['main'] += inv2.items['hotbar']
        sumInv.items['main'] += inv2.items['main']
        sumInv.items['main'] += [inv2.items['left'], inv2.items['right']]

        sumInv.sortItems()

        return sumInv

class Item:
    def __init__(self, resources):
        self.name = ''
        try:
            self.img = resources['item_'+self.getItemName()]
        except KeyError:
            import pygame
            self.img = pygame.image.load('resources/textures/mods/tiles/dirt.png')#.convert_alpha()
            #raise Exception('Item Image has not been Registered!')

    def getItemName(self):
        return self.name or 'null_item'

    def getMaxStackSize(self):
        return 1

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

    def getItem(self):
        return self.item

    def getMaxStackSize(self):
        return self.item.getMaxStackSize()

    def add(self, other):
        return [self, other]
