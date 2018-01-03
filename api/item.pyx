'''
item.py
A module to hold all the api stuff related to items
'''

class Inventory:
    def __init__(self):
        self.items = {'left' : ItemStack(Item({}), 1), 'right' : ItemStack(Item({}), 1), 'hotbar' : [], 'main' : []}

    def getEquipped(self):
        return [self.items['left'], self.items['right']]

    @staticmethod
    def fromBytes(byte):
        return Inventory()

    def toBytes(self):
        return b''

    def hashInv(self):
        '''
        Generate a hash of the contents of this inventory.
        Works regardless of the order and split of itemstacks
        '''
        # Duplicate the inventory
        newInv = self.duplicate()

        # Compress everything into a single list and sort
        newInv.items['main'] += newInv.items['hotbar']
        newInv.items['main'].append(newInv.items['right'])
        newInv.items['main'].append(newInv.items['left'])
        newInv.sortGroup('main', compress=True)

        # Separate the list
        itemlist = newInv.items['main']

        # TODO Hash the list
        return str(itemlist)

    def duplicate(self):
        '''
        Duplicate this inventory and return the copy
        '''
        newInv = Inventory()

        newInv.items['main'] = list(self.items['main'])
        newInv.items['hotbar'] = list(self.items['hotbar'])
        newInv.items['left'] = self.items['left']
        newInv.items['right'] = self.items['right']

        return newInv

    def sortItems(self, compress=False):
        '''
        Collect and sort the entire inventory
        '''
        self.sortGroup('hotbar', compress)
        self.sortGroup('main', compress)

    def sortGroup(self, name, compress=False):
        '''
        Collect and sort the given group in the inventory
        '''
        newGroup = []
        used = []
        for i, itemstack in enumerate(self.items[name]):
            if i in used or itemstack is None:
                continue
            for j, item in enumerate(self.items[name]):
                if item is not None and j != i and item.getItemName() == itemstack.getItemName():
                    used.append(j)
                    print(item, itemstack)
                    # result, carryover = itemstack.add(item)
                    newGroup += itemstack.add(item, compress)
                    # self.items[name][i] = result
                    # self.items[name][j] = carryover
        self.items[name] = sorted([a for a in newGroup if a])

    @staticmethod
    def addInventory(inv1, inv2, force=False):
        '''
        Return an inventory that is the sum of two inventories,
        and an overflow inventory for everything that doesn't fit
        '''
        sumInv = Inventory()
        overflowInv = Inventory()
        sumInv.items = inv1.items

        sumInv.items['main'] += inv2.items['hotbar']
        sumInv.items['main'] += inv2.items['main']
        sumInv.items['main'] += [inv2.items['left'], inv2.items['right']]

        if not force and len(sumInv.items['main']) > 24:
            # Overflow back into the original second inventory
            print('Inventory needs to overflow here...')
            overflowInv.items['main'] = sumInv.items['main'][24:]
            sumInv.items['main'] = sumInv.items['main'][:24]

        sumInv.sortItems()
        overflowInv.sortItems()

        return [sumInv, overflowInv]

class Item:
    def __init__(self, resources):
        self.name = ''
        try:
            self.img = resources['item_'+self.getItemName()]
        except KeyError:
            import pygame
            self.img = pygame.image.load('resources/textures/mods/tiles/dirt.png')
            #raise Exception('Item Image has not been Registered!')

    def setRegistryName(self, name):
        self.name = name

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

    def __lt__(self, other):
        if other is None:
            return True
        return self.item.getItemName() < other.item.getItemName()

    def __gt__(self, other):
        if other is None:
            return False
        return self.item.getItemName() > other.item.getItemName()

    def __str__(self):
        return 'ItemStack(item="{}", stackSize="{}")'.format(self.getItemName(), self.stackSize)

    def getItem(self):
        return self.item

    def getItemName(self):
        return self.getItem().getItemName()

    def getMaxStackSize(self):
        return self.item.getMaxStackSize()

    def add(self, other, forceCompress=False):
        '''
        Add one stack to another
        '''
        # Add the stack sizes and assign carryover as required
        sumSize = self.stackSize + other.stackSize
        carrySize = 0
        if not forceCompress and sumSize > self.getMaxStackSize():
            carrySize = sumSize%self.getMaxStackSize()
            sumSize = self.getMaxStackSize()

        # Create the stacks accordingly
        result = ItemStack(self.getItem(), sumSize)
        carryover = None
        if carrySize:
            carryover = ItemStack(self.getItem(), carrySize)

        return [result, carryover]
