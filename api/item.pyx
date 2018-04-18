'''
item.pyx
A module to hold all the api stuff related to items
'''
import random

from api import combat

class Inventory:
    def __init__(self):
        #Hotbar might be used in the future, but for now is useless
        self.items = {'left' : ItemStack(NullItem(), 0), 'right' : ItemStack(NullItem(), 0),
                      'armour' : ItemStack(NullItem(), 0), 'hotbar' : [], 'main' : []}
        self.maxSize = 999

    def getEquipped(self):
        return [self.items['left'], self.items['right'], self.items['armour']]

    def getItem(self, index):
        try:
            return self.items['main'][index]
        except IndexError:
            return ItemStack(NullItem(), 0)

    def toList(self):
        '''
        Return a list of every distinct itemstack in the inventory
        '''
        stacks = []
        stacks += self.items['main']
        stacks += self.items['hotbar']
        stacks.append(self.items['left'])
        stacks.append(self.items['right'])
        stacks.append(self.items['armour'])

        return stacks

    @staticmethod
    def fromBytes(game, bytes):
        '''
        Convert a transmitted byte string to an inventory object
        '''
        # Pull the inventory size of the top of the packet
        invSize = int.from_bytes(bytes[:2], 'big')
        bytes = bytes[2:]

        # Walk the bytestring and get the items
        armourLen = int.from_bytes(bytes[:2], 'big')
        armour = ItemStack.fromBytes(game, bytes[:armourLen+4])
        bytes = bytes[armourLen+4:]

        leftLen = int.from_bytes(bytes[:2], 'big')
        left = ItemStack.fromBytes(game, bytes[:leftLen+4])
        bytes = bytes[leftLen+4:]

        rightLen = int.from_bytes(bytes[:2], 'big')
        right = ItemStack.fromBytes(game, bytes[:rightLen+4])
        bytes = bytes[rightLen+4:]

        hotbar = []
        for a in range(10):
            itemLen = int.from_bytes(bytes[:2], 'big')
            hotbar.append(ItemStack.fromBytes(game, bytes[:itemLen+4]))
            bytes = bytes[itemLen+4:]

        main = []
        for a in range(invSize):
            itemLen = int.from_bytes(bytes[:2], 'big')
            main.append(ItemStack.fromBytes(game, bytes[:itemLen+4]))
            bytes = bytes[itemLen+4:]

        # Instantiate the inventory
        i = Inventory()
        # Set the values of the inventory
        i.maxSize = invSize
        i.items['armour'] = armour
        i.items['left'] = left
        i.items['right'] = right
        i.items['hotbar'] = hotbar
        i.items['main'] = main

        return i

    def toBytes(self):
        '''
        Convert the inventory to a byte string for transmission
        '''
        # Convert the equipped stacks
        armour, left, right = [self.items[a].toBytes() for a in ('armour', 'left', 'right')]

        # Then convert the hotbar and main sections
        hotbar = self.items['hotbar']
        hotbar += [ItemStack(NullItem(), 0)]*(10-len(hotbar))
        main = self.items['main']
        main += [ItemStack(NullItem(), 0)]*(self.maxSize-len(main))

        hotbar = b''.join([a.toBytes() for a in hotbar])
        main = b''.join([a.toBytes() for a in main])

        # Write it all out to a byte string
        return self.maxSize.to_bytes(2, 'big') + armour + left + right + hotbar + main

    def hashInv(self):
        '''
        Generate a hash of the contents of this inventory.
        Works regardless of the order and split of itemstacks
        '''
        # Duplicate the inventory
        newInv = self.duplicate()

        # Compress everything into a single list and sort
        newInv.items['main'] += newInv.items['hotbar']
        newInv.items['main'].append(newInv.items['left'])
        newInv.items['main'].append(newInv.items['right'])
        newInv.items['main'].append(newInv.items['armour'])
        newInv.sortGroup('main', compress=True)

        # Separate the list
        itemlist = newInv.items['main']

        # TODO Hash the list
        return str(itemlist)

    def duplicate(self):
        '''
        Duplicate this inventory and return the copy
        '''
        # Initialise the empty inventory
        newInv = Inventory()

        # Copy the each group into a new inventory
        newInv.items['main'] = list(self.items['main'])
        newInv.items['hotbar'] = list(self.items['hotbar'])
        newInv.items['left'] = self.items['left']
        newInv.items['right'] = self.items['right']
        newInv.items['armour'] = self.items['armour']

        return newInv

    def sortItems(self, compress=False):
        '''
        Collect and sort the entire inventory
        '''
        # Sort the two sections of the inventory separately
        self.sortGroup('hotbar', compress)
        self.sortGroup('main', compress)

    def sortGroup(self, name, compress=False):
        '''
        Collect and sort the given group in the inventory
        '''
        newGroup = []
        used = []
        # Iterate each item, find duplicate stacks and add them together
        for i, itemstack in enumerate(self.items[name]):
            if i in used or itemstack is None:
                continue
            for j, item in enumerate(self.items[name]):
                if item is not None and j != i and item.getRegistryName() == itemstack.getRegistryName():
                    used.append(j)
                    print(item, itemstack)
                    # result, carryover = itemstack.add(item)
                    newGroup += itemstack.add(item, compress)
                    # self.items[name][i] = result
                    # self.items[name][j] = carryover

        # Sort by item name
        self.items[name] = sorted([a for a in newGroup if a])

    def checkWeapon(self, weapon):
        '''
        Check if given weapon is equipped
        '''
        return weapon == self.items['left'].getItem() or weapon == self.items['right'].getItem()

    def addItemstack(self, itemstack):
        '''
        Add an itemstack to the main section of the inventory
        '''
        if len(self.items['main']) < self.maxSize:
            self.items['main'].append(itemstack)

        else:
            for i, stack in enumerate(self.items['main']):
                if stack.getRegistryName() == itemstack.getRegistryName():
                    result, carry = stack.add(itemstack)
                    if not carry:
                        self.items['main'][i] = result
                        return

                if stack.getRegistryName() == 'null_item':
                    self.items['main'][i] = itemstack
                    return

        print('[ERROR] New Itemstack cannot fit')

    @staticmethod
    def addInventory(inv1, inv2, force=False):
        '''
        Return an inventory that is the sum of two inventories,
        and an overflow inventory for everything that doesn't fit
        '''
        # Initialise the inventories
        sumInv = Inventory()
        overflowInv = Inventory()
        sumInv.items = inv1.items

        # Fill the first inventory's main section
        # with all of the second inventory's contents
        sumInv.items['main'] += inv2.items['hotbar']
        sumInv.items['main'] += inv2.items['main']
        sumInv.items['main'] += [inv2.items['left'], inv2.items['right'], inv2.items['armour']]

        # Sort and stack the itemstacks
        sumInv.sortItems()

        # Check if the inventory needs to overflow
        if not force and len(sumInv.items['main']) > inv1.maxSize:
            # Overflow back into the original second inventory
            print('Inventory needs to overflow here...')
            overflowInv.items['main'] = sumInv.items['main'][inv1.maxSize:]
            sumInv.items['main'] = sumInv.items['main'][:inv1.maxSize]

        # Sort the inventories
        sumInv.sortItems()
        overflowInv.sortItems()

        return [sumInv, overflowInv]

class PlayerInventory(Inventory):
    def __init__(self):
        super().__init__()
        self.maxSize = 16

class ItemStack:
    def __init__(self, item, size):
        self.stackSize = size
        self.item = item

    def __lt__(self, other):
        if other is None:
            return True
        return self.item.getRegistryName() < other.item.getRegistryName()

    def __gt__(self, other):
        if other is None:
            return False
        return self.item.getRegistryName() > other.item.getRegistryName()

    def __str__(self):
        return 'ItemStack(item="{}", stackSize="{}")'.format(self.getRegistryName(), self.stackSize)

    def toPickup(self, game, pos):
        '''
        Create a pickup entity corresponding to this ItemStack
        '''
        from api.entity import Pickup
        # Set up the pickup
        pickup = Pickup()
        pickup.setItemstack(self)

        # Generate a randomised position
        x, y = [int(a) for a in pos]
        decimal = round(random.random(), 2)
        pickup.pos = [random.randint(x-2, x+2)+decimal, random.randint(y-2, y+2)+decimal]

        # Assign it a UUID, and return it
        pickup.uuid = game.modLoader.getUUIDForEntity(pickup)
        return pickup

    @staticmethod
    def fromBytes(game, bytes):
        stack = ItemStack(None, 0)
        # Pull the stack size from the data
        stack.stackSize = int.from_bytes(bytes[2:4], 'big')
        bytes = bytes[4:]

        # Get the item from the data
        items = game.modLoader.gameRegistry.items.values()
        resources = game.modLoader.gameRegistry.resources
        stack.item = Item.fromBytes(items, resources, bytes)

        return stack

    def toBytes(self):
        itemBytes = self.item.toBytes()
        return len(itemBytes).to_bytes(2, 'big')+self.stackSize.to_bytes(2, 'big')+itemBytes

    def getItem(self):
        return self.item

    def getRegistryName(self):
        return self.getItem().getRegistryName()

    def getMaxStackSize(self):
        return self.item.getMaxStackSize()

    def getImage(self, resources):
        '''
        Return the image of the item in this stack
        '''
        return self.item.getImage(resources)

    def add(self, other, forceCompress=False):
        '''
        Add one stack to another
        '''
        # Add the stack sizes and assign carryover as required
        sumSize = self.stackSize + other.stackSize
        carrySize = 0
        if not forceCompress and sumSize > self.getMaxStackSize():
            carrySize = sumSize-self.getMaxStackSize()
            sumSize = self.getMaxStackSize()

        # Create the stacks accordingly
        result = ItemStack(self.getItem(), sumSize)
        carryover = None
        if carrySize:
            carryover = ItemStack(self.getItem(), carrySize)

        return [result, carryover]

class Item:
    def __init__(self):
        self.name = ''
        self.image = None

    def __eq__(self, other):
        if not isinstance(other, Item):
            return False
        return self.name == other.name

    def setRegistryName(self, name):
        self.name = name

    def getRegistryName(self):
        return self.name

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

    def getImage(self, resources):
        try:
            return resources[self.image]
        except KeyError:
            raise KeyError('Image "{}" has not been registered in the Game Registry'.format(self.image))

    def toBytes(self):
        '''
        Get a byte representation of the item
        '''
        className = self.__class__.__name__
        className = len(className).to_bytes(1, 'big')+className.encode()
        image = self.image if isinstance(self.image, str) else ''
        image = len(image).to_bytes(1, 'big')+image.encode()
        itemName = len(self.name).to_bytes(1, 'big')+self.name.encode()
        return itemName + image + className

    def fromBytes(itemClasses, resources, data):
        # Get the item name
        itemNameLen = data[0]
        itemName = data[1:1+itemNameLen].decode()
        data = data[1+itemNameLen:]

        # Get the item image
        imageLen = data[0]
        image = data[1:imageLen+1].decode()
        data = data[1+imageLen:]

        classLen = data[0]
        className = data[1:1+classLen].decode()
        data = data[1+classLen:]
        if data:
            # This is a weapon, decode accordingly
            itemTuple = (itemName, image, className)
            return Weapon.fromBytes(itemClasses, resources, data, itemTuple)

        # Iterate the possible classes and look for the matching item class
        for itemClass in itemClasses:
            if itemClass.__name__ == className:
                # Fill in the values for the item, then return it
                item = itemClass()
                item.name = itemName
                item.image = image
                return item

        return NullItem()

class Weapon(Item):
    def __init__(self):
        super().__init__()
        self.attack = 0
        self.damageClass = combat.NORMAL
        self.range = combat.MELEE
        self.knockback = combat.KNOCK_NONE
        self.spread = combat.WIDE_ARC

    def __eq__(self, other):
        if not isinstance(other, Weapon):
            return False
        varComparisons = [
                          self.attack == other.attack,
                          self.range == other.range,
                          self.knockback == other.knockback,
                          self.damageClass == other.damageClass,
                          self.spread == other.spread
                         ]
        return super().__eq__(other) and all(varComparisons)

    def toBytes(self):
        # Get the default item bytes
        itemData = super().toBytes()
        # Then append the weapon-specific information to it
        itemData += self.attack.to_bytes(3, 'big') + self.range.to_bytes(4, 'big')
        itemData += self.damageClass.to_bytes(1, 'big')
        itemData += self.knockback.to_bytes(2, 'big')
        return itemData

    def fromBytes(itemClasses, resources, data, itemTuple):
        itemName, image, className = itemTuple

        attack = int.from_bytes(data[:3], 'big')
        attackRange = int.from_bytes(data[3:7], 'big')
        damageClass = data[7]
        knockback = int.from_bytes(data[8:], 'big')

        # Iterate the possible classes and look for the matching item class
        for itemClass in itemClasses:
            if itemClass.__name__ == className:
                # Fill in the values for the item, then return it
                item = itemClass()
                item.name = itemName
                item.image = image
                item.attack = attack
                item.range = attackRange
                item.damageClass = damageClass
                item.knockback = knockback
                return item

        return NullItem()

    def calcDamage(self, game, source, entityList):
        '''
        Calculate the damage and call event hooks for this weapon
        against a list of entities
        '''
        for entity in entityList:
            damage = self.attack
            # TODO Apply Damage multipliers based on type

            # TODO Allow event hooks to modify the damage

            # Import the required classes late, since it crashes up the top
            from api.entity import Damage, Player, Entity
            from api.packets import ResetPlayerPacket

            if isinstance(entity, Player):
                game.getPlayer(entity.name).tickDamage = Damage(damage, source)

            elif isinstance(entity, Entity):
                game.getEntity(entity.uuid).tickDamage = Damage(damage, source)

class Armour(Item):
    pass

class NullItem(Item):
    '''
    A special item class used for empty itemslots
    '''
    def __init__(self):
        self.setRegistryName('null_item')
        self.image = None

    def getMaxStackSize(self):
        return 0

    def getImage(self, resources):
        return self.image
